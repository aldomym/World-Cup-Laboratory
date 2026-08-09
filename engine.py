from __future__ import annotations

import itertools
import math
import random
from copy import deepcopy
from data import TEAMS, TEAM_BY_ID, SLOT_CONFIG, RANKING_DATE

GROUP_LETTERS = list("ABCDEFGHIJKL")

def effective_rank(team):
    return team["fifaRank"] if team["fifaRank"] is not None else team.get("effectiveRank", 999)

def rating(team):
    # Compact synthetic rating derived from the locked July 2026 ranking.
    return 2200 - (effective_rank(team) - 1) * 6.0

def poisson(lam, rng):
    lam = max(0.05, lam)
    limit = math.exp(-lam)
    p = 1.0
    k = 0
    while p > limit:
        k += 1
        p *= rng.random()
    return k - 1

def simulate_match(home_id, away_id, rng, *, neutral=False, knockout=False, stage="", group=None):
    home = TEAM_BY_ID[home_id]
    away = TEAM_BY_ID[away_id]
    diff = rating(home) - rating(away)
    home_adv = 0.0 if neutral else 0.18
    home_lambda = min(3.6, max(0.22, 1.28 + diff / 620.0 + home_adv))
    away_lambda = min(3.4, max(0.20, 1.18 - diff / 690.0))
    hg = poisson(home_lambda, rng)
    ag = poisson(away_lambda, rng)
    result = {
        "stage": stage,
        "group": group,
        "homeId": home_id,
        "awayId": away_id,
        "homeGoals": hg,
        "awayGoals": ag,
        "extraTime": False,
        "penalties": None,
        "winnerId": None,
    }
    if knockout:
        if hg == ag:
            eth = poisson(home_lambda * 0.28, rng)
            eta = poisson(away_lambda * 0.28, rng)
            if eth or eta:
                result["extraTime"] = True
                hg += eth
                ag += eta
                result["homeGoals"] = hg
                result["awayGoals"] = ag
            if hg == ag:
                # Penalty shootout, slightly weighted by ranking.
                p_home = 1 / (1 + 10 ** ((rating(away) - rating(home)) / 900))
                home_pens = 3
                away_pens = 3
                while home_pens == away_pens:
                    home_pens = 3 + sum(rng.random() < (0.66 + 0.08 * p_home) for _ in range(3))
                    away_pens = 3 + sum(rng.random() < (0.74 - 0.08 * p_home) for _ in range(3))
                result["penalties"] = {"home": home_pens, "away": away_pens}
                result["winnerId"] = home_id if home_pens > away_pens else away_id
                return result
        result["winnerId"] = home_id if hg > ag else away_id
    return result

def make_standings(team_ids, matches):
    table = {
        tid: {"teamId": tid, "played": 0, "won": 0, "drawn": 0, "lost": 0,
              "gf": 0, "ga": 0, "gd": 0, "points": 0}
        for tid in team_ids
    }
    for m in matches:
        h, a = m["homeId"], m["awayId"]
        hg, ag = m["homeGoals"], m["awayGoals"]
        if h not in table or a not in table:
            continue
        table[h]["played"] += 1
        table[a]["played"] += 1
        table[h]["gf"] += hg
        table[h]["ga"] += ag
        table[a]["gf"] += ag
        table[a]["ga"] += hg
        if hg > ag:
            table[h]["won"] += 1
            table[a]["lost"] += 1
            table[h]["points"] += 3
        elif ag > hg:
            table[a]["won"] += 1
            table[h]["lost"] += 1
            table[a]["points"] += 3
        else:
            table[h]["drawn"] += 1
            table[a]["drawn"] += 1
            table[h]["points"] += 1
            table[a]["points"] += 1
    for row in table.values():
        row["gd"] = row["gf"] - row["ga"]
    return sorted(
        table.values(),
        key=lambda row: (
            row["points"], row["gd"], row["gf"],
            -effective_rank(TEAM_BY_ID[row["teamId"]])
        ),
        reverse=True,
    )

def seed_groups(team_ids, group_count, rng):
    ordered = sorted(team_ids, key=lambda tid: effective_rank(TEAM_BY_ID[tid]))
    groups = [[] for _ in range(group_count)]
    # Serpentine seeding gives each group a spread of strong and weak teams.
    for band_start in range(0, len(ordered), group_count):
        band = ordered[band_start:band_start + group_count]
        rng.shuffle(band)
        if (band_start // group_count) % 2:
            band.reverse()
        for i, tid in enumerate(band):
            groups[i % group_count].append(tid)
    return groups

def play_round_robin(team_ids, rng, stage, group):
    matches = []
    for a, b in itertools.combinations(team_ids, 2):
        if rng.random() < 0.5:
            a, b = b, a
        matches.append(simulate_match(a, b, rng, neutral=False, stage=stage, group=group))
    return matches

def initial_state(sim_id, name, year, host_id, seed, created_at):
    return {
        "id": sim_id,
        "name": name,
        "year": year,
        "hostId": host_id,
        "seed": seed,
        "status": "setup",
        "rankingDate": RANKING_DATE,
        "createdAt": created_at,
        "updatedAt": created_at,
        "qualifiers": None,
        "finalTeams": [],
        "pots": None,
        "groups": None,
        "tournament": None,
        "timeline": [
            {"label": "Simulation created", "detail": f"Host: {TEAM_BY_ID[host_id]['name']}"}
        ],
    }

def simulate_qualifiers(state):
    out = deepcopy(state)
    rng = random.Random(out["seed"] + 101)
    host = TEAM_BY_ID[out["hostId"]]
    all_matches = []
    confed_payload = {}
    direct_qualified = [host["id"]]
    playoff_candidates = []

    for confed, config in SLOT_CONFIG.items():
        confed_teams = [t for t in TEAMS if t["confederation"] == confed]
        contenders = [t["id"] for t in confed_teams if t["id"] != host["id"]]
        host_consumes = 1 if host["confederation"] == confed else 0
        direct_needed = max(0, config["direct"] - host_consumes)
        playoff_needed = config["playoff"]

        if confed == "CONMEBOL":
            group_ids = [contenders]
        else:
            group_count = max(1, direct_needed)
            group_ids = seed_groups(contenders, group_count, rng)

        group_results = []
        group_rankings = []
        for idx, tids in enumerate(group_ids):
            group_name = chr(65 + idx) if len(group_ids) <= 26 else str(idx + 1)
            matches = play_round_robin(tids, rng, f"{confed} qualifying", group_name)
            standings = make_standings(tids, matches)
            all_matches.extend(matches)
            group_results.append({"group": group_name, "teamIds": tids, "standings": standings})
            group_rankings.append(standings)

        confed_direct = []
        confed_playoff = []

        if confed == "CONMEBOL":
            standings = group_rankings[0]
            confed_direct = [r["teamId"] for r in standings[:direct_needed]]
            confed_playoff = [r["teamId"] for r in standings[direct_needed:direct_needed + playoff_needed]]
        elif direct_needed > 0:
            winners = [rows[0]["teamId"] for rows in group_rankings if rows]
            confed_direct = winners[:direct_needed]
            runnerups = [rows[1] for rows in group_rankings if len(rows) > 1]
            runnerups.sort(
                key=lambda row: (row["points"], row["gd"], row["gf"], -effective_rank(TEAM_BY_ID[row["teamId"]])),
                reverse=True,
            )
            confed_playoff = [r["teamId"] for r in runnerups[:playoff_needed]]
        else:
            merged = [row for rows in group_rankings for row in rows]
            merged.sort(
                key=lambda row: (row["points"], row["gd"], row["gf"], -effective_rank(TEAM_BY_ID[row["teamId"]])),
                reverse=True,
            )
            confed_playoff = [r["teamId"] for r in merged[:playoff_needed]]

        direct_qualified.extend(confed_direct)
        playoff_candidates.extend(confed_playoff)
        confed_payload[confed] = {
            "directSlots": config["direct"],
            "playoffSlots": playoff_needed,
            "hostSlotConsumed": bool(host_consumes),
            "groups": group_results,
            "directQualified": confed_direct,
            "playoffCandidates": confed_playoff,
        }

    if len(playoff_candidates) != 6:
        raise RuntimeError(f"Expected 6 intercontinental playoff candidates, got {len(playoff_candidates)}")

    seeded = sorted(playoff_candidates, key=lambda tid: effective_rank(TEAM_BY_ID[tid]))[:2]
    unseeded = [tid for tid in playoff_candidates if tid not in seeded]
    rng.shuffle(unseeded)
    semi1 = simulate_match(unseeded[0], unseeded[1], rng, neutral=True, knockout=True,
                           stage="Intercontinental playoff semifinal")
    semi2 = simulate_match(unseeded[2], unseeded[3], rng, neutral=True, knockout=True,
                           stage="Intercontinental playoff semifinal")
    finalists = [semi1["winnerId"], semi2["winnerId"]]
    rng.shuffle(finalists)
    final1 = simulate_match(seeded[0], finalists[0], rng, neutral=True, knockout=True,
                            stage="Intercontinental playoff final")
    final2 = simulate_match(seeded[1], finalists[1], rng, neutral=True, knockout=True,
                            stage="Intercontinental playoff final")
    playoff_winners = [final1["winnerId"], final2["winnerId"]]
    final_teams = direct_qualified + playoff_winners

    if len(final_teams) != 48 or len(set(final_teams)) != 48:
        raise RuntimeError(f"Qualifier engine produced {len(set(final_teams))} unique finalists, expected 48")

    out["qualifiers"] = {
        "confederations": confed_payload,
        "matches": all_matches,
        "intercontinental": {
            "candidates": playoff_candidates,
            "seeded": seeded,
            "matches": [semi1, semi2, final1, final2],
            "winners": playoff_winners,
        },
        "directQualified": direct_qualified,
    }
    out["finalTeams"] = final_teams
    out["pots"] = None
    out["groups"] = None
    out["tournament"] = None
    out["status"] = "qualified"
    out["timeline"].append({
        "label": "Qualifiers completed",
        "detail": f"48-team field locked; {len(all_matches) + 4} qualifier/playoff results saved."
    })
    return out

def can_join_group(team_id, group):
    confed = TEAM_BY_ID[team_id]["confederation"]
    count = sum(TEAM_BY_ID[t]["confederation"] == confed for t in group)
    return count < (2 if confed == "UEFA" else 1)

def _assign_pot(teams, groups, rng, idx=0):
    if idx >= len(teams):
        return True
    team_id = teams[idx]
    candidates = list(range(12))
    rng.shuffle(candidates)
    candidates.sort(key=lambda gi: len(groups[gi]))
    for gi in candidates:
        if len(groups[gi]) >= 4:
            continue
        if can_join_group(team_id, groups[gi]):
            groups[gi].append(team_id)
            if _assign_pot(teams, groups, rng, idx + 1):
                return True
            groups[gi].pop()
    return False

def perform_draw(state):
    if len(state.get("finalTeams") or []) != 48:
        raise ValueError("Complete qualifiers before running the final draw.")
    out = deepcopy(state)
    rng = random.Random(out["seed"] + 202)
    ordered = sorted(out["finalTeams"], key=lambda tid: effective_rank(TEAM_BY_ID[tid]))
    pots = [ordered[i:i + 12] for i in range(0, 48, 12)]

    groups = [[] for _ in range(12)]
    p1 = pots[0][:]
    rng.shuffle(p1)
    for gi, tid in enumerate(p1):
        groups[gi].append(tid)

    for pot in pots[1:]:
        success = False
        for _ in range(120):
            candidate_groups = [g[:] for g in groups]
            teams = pot[:]
            rng.shuffle(teams)
            if _assign_pot(teams, candidate_groups, rng):
                groups = candidate_groups
                success = True
                break
        if not success:
            raise RuntimeError("Could not create a confederation-valid draw. Try a new simulation seed.")

    out["pots"] = [{"pot": i + 1, "teamIds": pot} for i, pot in enumerate(pots)]
    out["groups"] = [{"group": GROUP_LETTERS[i], "teamIds": groups[i]} for i in range(12)]
    out["tournament"] = None
    out["status"] = "drawn"
    out["timeline"].append({
        "label": "Final draw completed",
        "detail": "Four ranking-based pots of 12 drawn into Groups A–L."
    })
    return out

def _performance_key(row):
    return (row["points"], row["gd"], row["gf"], -effective_rank(TEAM_BY_ID[row["teamId"]]))

def simulate_final_tournament(state):
    if not state.get("groups") or len(state["groups"]) != 12:
        raise ValueError("Run the 48-team draw before simulating the final tournament.")
    out = deepcopy(state)
    rng = random.Random(out["seed"] + 303)
    group_matches = []
    group_tables = []
    qualified = []
    thirds = []

    for group in out["groups"]:
        letter = group["group"]
        tids = group["teamIds"]
        matches = []
        for a, b in itertools.combinations(tids, 2):
            matches.append(simulate_match(a, b, rng, neutral=True, stage="World Cup group stage", group=letter))
        standings = make_standings(tids, matches)
        group_matches.extend(matches)
        group_tables.append({"group": letter, "standings": standings})
        for row in standings[:2]:
            qualified.append({**row, "group": letter, "position": 1 if row is standings[0] else 2})
        thirds.append({**standings[2], "group": letter, "position": 3})

    thirds.sort(key=_performance_key, reverse=True)
    qualified.extend(thirds[:8])
    qualified.sort(
        key=lambda row: (
            1 if row["position"] == 1 else 0,
            row["points"], row["gd"], row["gf"],
            -effective_rank(TEAM_BY_ID[row["teamId"]])
        ),
        reverse=True,
    )

    top = qualified[:16]
    bottom = list(reversed(qualified[16:]))
    pairs = []
    for seed_row in top:
        pick = next((i for i, row in enumerate(bottom) if row["group"] != seed_row["group"]), 0)
        opp = bottom.pop(pick)
        pairs.append((seed_row["teamId"], opp["teamId"]))

    rounds = []
    current = []
    for a, b in pairs:
        current.append(simulate_match(a, b, rng, neutral=True, knockout=True, stage="Round of 32"))
    rounds.append({"round": "Round of 32", "matches": current})

    round_names = ["Round of 16", "Quarterfinals", "Semifinals"]
    semifinal_losers = []
    for round_name in round_names:
        winners = [m["winnerId"] for m in current]
        next_matches = []
        for i in range(0, len(winners), 2):
            match = simulate_match(winners[i], winners[i + 1], rng, neutral=True, knockout=True, stage=round_name)
            next_matches.append(match)
        if round_name == "Semifinals":
            for m in next_matches:
                semifinal_losers.append(m["awayId"] if m["winnerId"] == m["homeId"] else m["homeId"])
        current = next_matches
        rounds.append({"round": round_name, "matches": current})

    finalists = [m["winnerId"] for m in current]
    final = simulate_match(finalists[0], finalists[1], rng, neutral=True, knockout=True, stage="Final")
    rounds.append({"round": "Final", "matches": [final]})
    third_place = simulate_match(semifinal_losers[0], semifinal_losers[1], rng, neutral=True,
                                 knockout=True, stage="Third-place playoff")

    out["tournament"] = {
        "groupMatches": group_matches,
        "groupTables": group_tables,
        "bestThirdPlaced": [r["teamId"] for r in thirds[:8]],
        "knockoutRounds": rounds,
        "thirdPlaceMatch": third_place,
        "championId": final["winnerId"],
    }
    out["status"] = "completed"
    out["timeline"].append({
        "label": "Tournament completed",
        "detail": f"Champion: {TEAM_BY_ID[final['winnerId']]['name']}."
    })
    return out

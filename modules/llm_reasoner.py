"""
==========================================================
UrbanRoof AI DDR Generator

LLM Reasoning Engine

Uses Gemini 2.5 Pro

Responsible for:
- Executive Summary
- Root Cause Analysis
- Severity Classification
- Recommendations
- Overall Building Health

Author: Adithya Sapalya
==========================================================
"""

from __future__ import annotations

import json
import time

import os
from groq import Groq

from modules.knowledge_base import (

    KnowledgeBase,

    Observation

)

from config import (

    GROQ_API_KEY,

    GEMINI_MODEL

)


# ==========================================================
# Gemini Configuration
# ==========================================================

groq_client = Groq(

    api_key=GROQ_API_KEY

)


# ==========================================================
# LLM Reasoner
# ==========================================================

class LLMReasoner:

    def __init__(self):

        print("\nLoading Groq...")

        self.model = groq_client

        print(

            f"Model Loaded : {GROQ_API_KEY}"

        )


    # ------------------------------------------------------
    # Observation -> Prompt
    # ------------------------------------------------------

    def observation_prompt(

        self,

        observation: Observation

    ) -> str:

        return f"""
You are a senior structural engineer.

Analyse the following building observation.

Return ONLY valid JSON.

Observation

Area:
{observation.area}

Issue:
{observation.issue}

Description:
{observation.description}

Evidence:
{observation.source_evidence}

Matched Observation:
{observation.matched_observation_id}

Similarity:
{observation.similarity_score}


Return JSON ONLY

{{
    "severity":"",
    "root_cause":"",
    "recommendation":""
}}

Do not explain.

Do not write markdown.

Return JSON only.
"""


    # ------------------------------------------------------
    # Safe JSON Parser
    # ------------------------------------------------------

    def parse_json(

        self,

        text

    ):

        text = text.strip()

        if text.startswith("```"):

            text = text.replace(

                "```json",

                ""

            )

            text = text.replace(

                "```",

                ""

            )

        start = text.find("{")

        end = text.rfind("}")

        if start == -1 or end == -1:

            return None

        try:

            return json.loads(

                text[start:end + 1]

            )

        except Exception:

            return None


    # ------------------------------------------------------
    # Ask Gemini
    # ------------------------------------------------------

    def ask(

        self,

        prompt,

        retries=3

    ):

        for attempt in range(retries):

            try:

                response = self.model.generate_content(

                    prompt

                )

                result = self.parse_json(

                    response.text

                )

                if result is not None:

                    return result

            except Exception as e:

                print(

                    f"Gemini Error : {e}"

                )

            time.sleep(2)

        return None
    # ------------------------------------------------------
    # Reason One Observation
    # ------------------------------------------------------

    def reason_observation(

        self,

        observation: Observation

    ) -> Observation:

        prompt = self.observation_prompt(

            observation

        )

        result = self.ask(

            prompt

        )

        if result is None:

            print(

                f"Failed to analyse Observation {observation.id}"

            )

            return observation

        observation.severity = result.get(

            "severity",

            "Unknown"

        )

        observation.root_cause = result.get(

            "root_cause",

            ""

        )

        observation.recommendation = result.get(

            "recommendation",

            ""

        )

        return observation

    # ------------------------------------------------------
    # Reason All Observations
    # ------------------------------------------------------

    def reason_all_observations(

        self,

        kb: KnowledgeBase

    ) -> KnowledgeBase:

        observations = kb.get_all_observations()

        print()

        print("=" * 60)

        print("LLM REASONING")

        print("=" * 60)

        print(

            f"Observations : {len(observations)}"

        )

        for index, observation in enumerate(

            observations,

            start=1

        ):

            print(

                f"[{index}/{len(observations)}] "

                f"{observation.area} - "

                f"{observation.issue}"

            )

            self.reason_observation(

                observation

            )

        print()

        print("Observation reasoning completed.")

        return kb

    # ------------------------------------------------------
    # Count Severity Levels
    # ------------------------------------------------------

    def severity_statistics(

        self,

        kb: KnowledgeBase

    ):

        stats = {

            "Critical": 0,

            "High": 0,

            "Medium": 0,

            "Low": 0,

            "Unknown": 0

        }

        for obs in kb.get_all_observations():

            severity = obs.severity.strip().title()

            if severity not in stats:

                severity = "Unknown"

            stats[severity] += 1

        return stats

    # ------------------------------------------------------
    # Building Health Score
    # ------------------------------------------------------

    def building_health_score(

        self,

        kb: KnowledgeBase

    ) -> int:

        stats = self.severity_statistics(

            kb

        )

        score = 100

        score -= stats["Critical"] * 20

        score -= stats["High"] * 10

        score -= stats["Medium"] * 5

        score -= stats["Low"] * 2

        score = max(

            score,

            0

        )

        return score
    # ------------------------------------------------------
    # Executive Summary Prompt
    # ------------------------------------------------------

    def executive_summary_prompt(

        self,

        kb: KnowledgeBase

    ) -> str:

        observations = kb.get_all_observations()

        summary = ""

        for obs in observations:

            summary += f"""

Area: {obs.area}

Issue: {obs.issue}

Severity: {obs.severity}

Root Cause: {obs.root_cause}

Recommendation: {obs.recommendation}

"""

        return f"""
You are a Senior Structural Engineer.

Generate an executive summary for the following property inspection.

Return ONLY JSON.

Inspection Findings:

{summary}

Return:

{{
    "overall_condition":"",
    "executive_summary":"",
    "priority_actions":[]
}}

The executive summary should be less than 200 words.

Return JSON only.
"""

    # ------------------------------------------------------
    # Executive Summary
    # ------------------------------------------------------

    def generate_executive_summary(

        self,

        kb: KnowledgeBase

    ):

        prompt = self.executive_summary_prompt(

            kb

        )

        result = self.ask(

            prompt

        )

        if result is None:

            return {

                "overall_condition": "Unknown",

                "executive_summary": "",

                "priority_actions": []

            }

        return result

    # ------------------------------------------------------
    # Save LLM Output
    # ------------------------------------------------------

    def save_results(

        self,

        kb: KnowledgeBase,

        output_file

    ):

        observations = []

        for obs in kb.get_all_observations():

            observations.append({

                "id": obs.id,

                "source": obs.source,

                "area": obs.area,

                "issue": obs.issue,

                "description": obs.description,

                "severity": obs.severity,

                "root_cause": obs.root_cause,

                "recommendation": obs.recommendation,

                "matched_observation_id": obs.matched_observation_id,

                "similarity_score": obs.similarity_score

            })

        report = {

            "health_score": self.building_health_score(

                kb

            ),

            "severity_statistics": self.severity_statistics(

                kb

            ),

            "executive_summary": self.generate_executive_summary(

                kb

            ),

            "observations": observations

        }

        with open(

            output_file,

            "w",

            encoding="utf-8"

        ) as f:

            json.dump(

                report,

                f,

                indent=4,

                ensure_ascii=False

            )

        print(

            f"LLM reasoning saved -> {output_file}"

        )

        return report

    # ------------------------------------------------------
    # Full Pipeline
    # ------------------------------------------------------

    def run(

        self,

        kb: KnowledgeBase,

        output_file="output/llm_reasoning.json"

    ):

        print()

        print("=" * 60)

        print("LLM REASONING")

        print("=" * 60)

        kb = self.reason_all_observations(

            kb

        )

        report = self.save_results(

            kb,

            output_file

        )

        print()

        print("=" * 60)

        print("LLM Reasoning Completed")

        print("=" * 60)

        print()

        return kb, report    
"""
==========================================================
UrbanRoof AI DDR Generator

Gemini Reasoning Module
==========================================================
"""

import json
import google.generativeai as genai

from modules.knowledge_base import KnowledgeBase

from config import GEMINI_API_KEY, GEMINI_MODEL


class LLMReasoner:

    def __init__(self):

        genai.configure(api_key=GEMINI_API_KEY)

        self.model = genai.GenerativeModel(GEMINI_MODEL)

    # ----------------------------------------------------

    def build_prompt(

        self,

        inspection,

        thermal

    ):

        return f"""
You are a senior building inspection engineer.

Compare the following findings.

Inspection Finding

Area:
{inspection.area}

Issue:
{inspection.issue}

Description:
{inspection.description}

Evidence:
{inspection.source_evidence}


Thermal Finding

Area:
{thermal.area}

Issue:
{thermal.issue}

Description:
{thermal.description}

Evidence:
{thermal.source_evidence}


Return ONLY JSON.

{{
"summary":"",
"root_cause":"",
"severity":"",
"recommendation":""
}}
"""

    # ----------------------------------------------------

    def run(

        self,

        kb: KnowledgeBase

    ):

        thermal_lookup = {

            obs.id: obs

            for obs in kb.thermal_observations

        }

        for inspection in kb.inspection_observations:

            if inspection.matched_observation_id is None:

                continue

            thermal = thermal_lookup.get(

                inspection.matched_observation_id

            )

            if thermal is None:

                continue

            prompt = self.build_prompt(

                inspection,

                thermal

            )

            response = self.model.generate_content(

                prompt

            )

            text = response.text.strip()

            text = text.replace("```json","")

            text = text.replace("```","")

            try:

                result = json.loads(text)

            except Exception:

                print("Gemini returned invalid JSON.")

                continue

            inspection.root_cause = result.get(

                "root_cause",

                ""

            )

            inspection.recommendation = result.get(

                "recommendation",

                ""

            )

            inspection.severity = result.get(

                "severity",

                ""

            )

            inspection.description += (

                "\n\nAI Summary:\n"

                +

                result.get(

                    "summary",

                    ""

                )

            )

        return kb
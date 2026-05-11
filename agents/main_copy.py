"""
SamenOntzorgen — AI Team (Multi-Project)
Eisenhower is de command center die werk naar de juiste project manager stuurt.

Gebruik:
    python main.py

Vereisten:
    1. Kopieer .env.example naar .env
    2. Vul je ANTHROPIC_API_KEY in
    3. pip install -r requirements.txt
"""

import anyio
import os
from dotenv import load_dotenv
from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AgentDefinition,
    ResultMessage,
)
from prompts import (
    EISENHOWER_PROMPT,
    LARRY_PROMPT, BAX_PROMPT, SAM_PROMPT, NOVA_PROMPT, NOLAN_PROMPT,
    VERA_PROMPT, FINN_PROMPT, ROSA_PROMPT, DAAN_PROMPT, LENA_PROMPT,
    BRAM_PROMPT, IRIS_PROMPT,
    MARINA_PROMPT,
    SOPHIA_PROMPT,
    ADMIN_PROMPT,
    # Matti team
    ARIA_PROMPT, LIAM_PROMPT, SOPHIE_PROMPT, JOSH_PROMPT, MAYA_PROMPT,
    ZOE_PROMPT, ALEX_PROMPT, JORDAN_PROMPT, CASEY_PROMPT, RILEY_PROMPT,
    # AI Doc team
    ESTHER_PROMPT, SEBASTIAN_PROMPT, HENRI_PROMPT, CLAIRE_PROMPT,
    LUCAS_PROMPT, MARIE_PROMPT, THOMAS_PROMPT, ALICE_PROMPT,
    FRANÇOIS_PROMPT, NOAH_PROMPT,
)

load_dotenv()


def check_api_key():
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n❌ ANTHROPIC_API_KEY niet gevonden.")
        print("   1. Kopieer .env.example naar .env")
        print("   2. Vul je API key in op https://console.anthropic.com")
        print("   3. Start het programma opnieuw\n")
        return False
    return True


def print_welkom():
    print("\n" + "=" * 60)
    print("  EISENHOWER — COMMAND CENTER")
    print("  Multi-Project AI Team Orchestrator")
    print("=" * 60)
    print("  Projecten: SamenOntzorgen (11) | Matti (11) | AI Doc (10) | Admin (5)")
    print("  Totaal: 37 agents")
    print("  Typ 'stop' om te stoppen.")
    print("=" * 60 + "\n")


async def vraag_eisenhower(gebruikersinput: str) -> str:
    resultaat = ""

    async for bericht in query(
        prompt=gebruikersinput,
        options=ClaudeAgentOptions(
            system_prompt=EISENHOWER_PROMPT,
            allowed_tools=["Agent"],
            agents={
                # ─────────────────────────────────
                # SAMENONTZORGEN PROJECT MANAGER
                # ─────────────────────────────────
                "larry": AgentDefinition(
                    description=(
                        "Larry is Project Manager voor SamenOntzorgen. "
                        "Schakel Larry in voor: coöperatief model, ZZP'ers, zorginstellingen, "
                        "Wet DBA, VBAR, LinkedIn outreach, Facebook outreach."
                    ),
                    prompt=LARRY_PROMPT,
                    tools=["Agent"],
                ),
                "bax": AgentDefinition(
                    description=(
                        "Bax is Senior Onderzoeker. Research: sectordata, PNIL-kosten, "
                        "marktcijfers, Wet DBA, VBAR, skills voor nieuwe teamleden."
                    ),
                    prompt=BAX_PROMPT,
                    tools=["WebSearch", "WebFetch"],
                ),
                "sam": AgentDefinition(
                    description=(
                        "Sam is LinkedIn Outreach Specialist. Schrijft connectieverzoeken "
                        "en follow-ups voor HR-directeuren en bestuurders bij zorginstellingen."
                    ),
                    prompt=SAM_PROMPT,
                    tools=[],
                ),
                "nova": AgentDefinition(
                    description=(
                        "Nova is Deal Coach. Bereidt Wim voor op verkoopgesprekken, "
                        "pilot-onderhandelingen, bezwaarscripts."
                    ),
                    prompt=NOVA_PROMPT,
                    tools=[],
                ),
                "nolan": AgentDefinition(
                    description=(
                        "Nolan is HR Directeur. Maakt nieuwe AI teamleden aan "
                        "met profiel en systeemprompt."
                    ),
                    prompt=NOLAN_PROMPT,
                    tools=["Write"],
                ),
                "vera": AgentDefinition(
                    description=(
                        "Vera is Content Strateeg. Schrijft LinkedIn posts, nieuwsbrief, "
                        "blogs over flex-arbeid, VBAR, coöperatie model."
                    ),
                    prompt=VERA_PROMPT,
                    tools=[],
                ),
                "finn": AgentDefinition(
                    description=(
                        "Finn is LinkedIn Netwerk Specialist. Warm netwerk outreach, "
                        "InMails, connectieverzoeken — altijd met goedkeuring."
                    ),
                    prompt=FINN_PROMPT,
                    tools=["Read", "Computer"],
                ),
                "rosa": AgentDefinition(
                    description=(
                        "Rosa is Facebook Content Specialist. Schrijft Facebook posts "
                        "voor ZZP'ers en deeltijdwerkers in de zorg."
                    ),
                    prompt=ROSA_PROMPT,
                    tools=[],
                ),
                "daan": AgentDefinition(
                    description=(
                        "Daan is Facebook Outreach Specialist. DMs, groepsreacties, "
                        "verwelkoming nieuwe leden — altijd met goedkeuring."
                    ),
                    prompt=DAAN_PROMPT,
                    tools=["Computer"],
                ),
                "lena": AgentDefinition(
                    description=(
                        "Lena is Intake Specialist. Begeleidt zorgprofessionals naar "
                        "gratis lidmaatschap van SamenOntzorgen."
                    ),
                    prompt=LENA_PROMPT,
                    tools=["Write"],
                ),
                "iris": AgentDefinition(
                    description=(
                        "Iris is Prospect Researcher. Opspoort huisartsenpraktijken "
                        "met contactgegevens voor Bram."
                    ),
                    prompt=IRIS_PROMPT,
                    tools=["WebSearch", "WebFetch", "Write"],
                ),
                "bram": AgentDefinition(
                    description=(
                        "Bram is Huisartsen Outreach Specialist. LinkedIn en e-mail "
                        "berichten naar huisartsen en praktijken — altijd met goedkeuring."
                    ),
                    prompt=BRAM_PROMPT,
                    tools=["Computer"],
                ),

                # ─────────────────────────────────
                # MATTI PROJECT MANAGER
                # ─────────────────────────────────
                "marina": AgentDefinition(
                    description=(
                        "Marina is Project Manager voor Matti (app voor jongeren 12-21). "
                        "Schakel Marina in voor: app features, school outreach, jongeren-content, "
                        "community management, peer-to-peer messaging."
                    ),
                    prompt=MARINA_PROMPT,
                    tools=["Agent"],
                ),
                "aria": AgentDefinition(
                    description=(
                        "Aria is Strategist voor Matti. Pillar 1 eigenaar, positionering, "
                        "tone bewaakt, landing page copy, social strategie."
                    ),
                    prompt=ARIA_PROMPT,
                    tools=[],
                ),
                "liam": AgentDefinition(
                    description=(
                        "Liam is App Designer voor Matti. UX/UI design, features, flows, "
                        "themes, mobile-first design voor jongeren."
                    ),
                    prompt=LIAM_PROMPT,
                    tools=[],
                ),
                "sophie": AgentDefinition(
                    description=(
                        "Sophie is School Outreach Specialist. Scholen benaderen voor pilots, "
                        "directeuren, mentoren, pilot-voorstellen."
                    ),
                    prompt=SOPHIE_PROMPT,
                    tools=[],
                ),
                "josh": AgentDefinition(
                    description=(
                        "Josh is Instagram Creator. Instagram content voor jongeren: "
                        "posts, stories, reels over mentale gezondheid."
                    ),
                    prompt=JOSH_PROMPT,
                    tools=[],
                ),
                "maya": AgentDefinition(
                    description=(
                        "Maya is Community Manager. Discord community modereren, "
                        "engagement, onboarding, feedback voor Matti."
                    ),
                    prompt=MAYA_PROMPT,
                    tools=[],
                ),
                "zoe": AgentDefinition(
                    description=(
                        "Zoe is TikTok Creator. TikTok content: korte video's, trends, "
                        "virale content over mentale gezondheid voor jongeren."
                    ),
                    prompt=ZOE_PROMPT,
                    tools=[],
                ),
                "alex": AgentDefinition(
                    description=(
                        "Alex is Safety Monitor. Feedback analyseren, risico's detecteren, "
                        "safety protocols, escalation naar professionals."
                    ),
                    prompt=ALEX_PROMPT,
                    tools=[],
                ),
                "jordan": AgentDefinition(
                    description=(
                        "Jordan is Parent Liaison. Brug tussen Matti en Opvoedmaatje, "
                        "ouder-content, educatie over jongeren mentale gezondheid."
                    ),
                    prompt=JORDAN_PROMPT,
                    tools=[],
                ),
                "casey": AgentDefinition(
                    description=(
                        "Casey is Integration Specialist. Matti app ↔ dashboard coupling, "
                        "API keys, data flow, user sync tussen app en dashboard."
                    ),
                    prompt=CASEY_PROMPT,
                    tools=[],
                ),
                "riley": AgentDefinition(
                    description=(
                        "Riley is Quality Lead. Tone review, content consistency, "
                        "quality control voor alle Matti-content."
                    ),
                    prompt=RILEY_PROMPT,
                    tools=[],
                ),

                # ─────────────────────────────────
                # AI DOC PROJECT MANAGER
                # ─────────────────────────────────
                "sophia": AgentDefinition(
                    description=(
                        "Sophia is Project Manager voor AI Doc / PraktijkAssistent. "
                        "Schakel Sophia in voor: huisartsenpraktijken, SOEP-notes, "
                        "genderbias alerts, medische content, praktijk outreach."
                    ),
                    prompt=SOPHIA_PROMPT,
                    tools=["Agent"],
                ),
                "esther": AgentDefinition(
                    description=(
                        "Esther is Medical Strategist. Pillar 1 eigenaar, medische positionering, "
                        "correctheid bewaakt, compliance, huisartsenperspectief."
                    ),
                    prompt=ESTHER_PROMPT,
                    tools=[],
                ),
                "sebastian": AgentDefinition(
                    description=(
                        "Sebastian is Medical Researcher. SOEP-guidelines, genderbias evidence, "
                        "medische literatuur review, evidence compilation."
                    ),
                    prompt=SEBASTIAN_PROMPT,
                    tools=["WebSearch", "WebFetch"],
                ),
                "henri": AgentDefinition(
                    description=(
                        "Henri is GP Outreach Specialist. Huisartsenpraktijken benaderen, "
                        "praktijkhouders outreach, pilot-voorstellen."
                    ),
                    prompt=HENRI_PROMPT,
                    tools=[],
                ),
                "claire": AgentDefinition(
                    description=(
                        "Claire is Workflow Designer. SOEP-workflows ontwerpen, "
                        "AI Doc integratie in praktijk, user flows, training."
                    ),
                    prompt=CLAIRE_PROMPT,
                    tools=[],
                ),
                "lucas": AgentDefinition(
                    description=(
                        "Lucas is Gender Bias Expert. Bias alerts ontwikkelen, "
                        "onderdiagnose educatie, evidence-based alerts."
                    ),
                    prompt=LUCAS_PROMPT,
                    tools=[],
                ),
                "marie": AgentDefinition(
                    description=(
                        "Marie is Compliance Officer. Privacy, liability, AVG, "
                        "medische regelgeving compliance voor AI Doc."
                    ),
                    prompt=MARIE_PROMPT,
                    tools=[],
                ),
                "thomas": AgentDefinition(
                    description=(
                        "Thomas is Practice Manager Contact. Praktijkmanagers benaderen, "
                        "operations-focussed outreach, digital adoption."
                    ),
                    prompt=THOMAS_PROMPT,
                    tools=[],
                ),
                "alice": AgentDefinition(
                    description=(
                        "Alice is Patient Liaison. Patiënt-uitleg verbeteren, "
                        "empathische communicatie templates, inclusiviteit."
                    ),
                    prompt=ALICE_PROMPT,
                    tools=[],
                ),
                "françois": AgentDefinition(
                    description=(
                        "François is Medical Content Creator. Blogs, whitepapers, "
                        "educational content over AI in huisartsenzorg."
                    ),
                    prompt=FRANÇOIS_PROMPT,
                    tools=[],
                ),
                "noah": AgentDefinition(
                    description=(
                        "Noah is Implementation Specialist. Praktijken onboarden, "
                        "training, support, feedback collection voor AI Doc."
                    ),
                    prompt=NOAH_PROMPT,
                    tools=[],
                ),

                # ─────────────────────────────────
                # ADMIN / META PROJECT
                # ─────────────────────────────────
                "admin": AgentDefinition(
                    description=(
                        "Admin handelt meta-taken af: documentatie, processen, "
                        "planning, strategische reflectie, tools setup."
                    ),
                    prompt=ADMIN_PROMPT,
                    tools=["Write", "Read"],
                ),
            },
            max_turns=20,
        ),
    ):
        if isinstance(bericht, ResultMessage):
            resultaat = bericht.result

    return resultaat


async def main():
    if not check_api_key():
        return

    print_welkom()

    while True:
        try:
            gebruikersinput = input("Wim: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nEisenhower: Tot de volgende keer!")
            break

        if not gebruikersinput:
            continue

        if gebruikersinput.lower() in ["stop", "exit", "quit", "bye"]:
            print("\nEisenhower: Tot de volgende keer, Wim!")
            break

        print("\nEisenhower: Bepaal de route...\n")

        try:
            antwoord = await vraag_eisenhower(gebruikersinput)
            print(f"Eisenhower: {antwoord}\n")
        except Exception as fout:
            print(f"\n❌ Fout: {fout}\n")


if __name__ == "__main__":
    anyio.run(main)

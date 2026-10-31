"""Vérifie le guide contextuel embarqué (contextes, règles, erreurs)."""

import asyncio

from test_utils import run_event

from app.guide_hints import CONTEXTS, TOPIC_HINTS
from app.states.help_state import HelpState


async def main():
    print("=== Test guide contextuel intelligent ===")
    state = HelpState()

    assert state.is_open is False, "Le panneau est fermé au départ"

    # Chaque contexte d'écran doit remonter du contenu réel de la base.
    for key in CONTEXTS:
        await run_event(state.open_context, key)
        assert state.is_open is True, f"Panneau ouvert attendu pour {key}"
        assert state.is_loading is False, "Le chargement doit être terminé"
        assert state.context_label != "", f"Libellé manquant pour {key}"
        assert state.context_key == key
        assert state.content_count > 0, f"Aucun contenu pour le contexte {key}"
        assert len(state.rules) > 0, f"Aucune règle pour {key}"
        assert len(state.articles) > 0, f"Aucun article pour {key}"
        print(
            f"  · {key}: {len(state.concepts)} concepts, {len(state.rules)} règles, {len(state.faqs)} questions, {len(state.procedures)} procédures, {len(state.articles)} articles"
        )

    # Fermeture / bascule.
    await run_event(state.toggle_context, state.context_key)
    assert state.is_open is False, "La bascule doit refermer le panneau"

    # Sujets de règle utilisés pour enrichir les erreurs de formulaires.
    for topic in TOPIC_HINTS:
        await run_event(state.open_topic, "parcelles", topic)
        assert state.has_focus is True, f"Focus attendu pour {topic}"
        assert state.focus_hint != "", f"Explication manquante pour {topic}"
        assert len(state.focus_rules) > 0, (
            f"Aucune règle de cohérence trouvée pour le sujet {topic}"
        )
        codes = [rule["code"] for rule in state.focus_rules]
        for code in codes:
            assert code != "", "Code de règle vide"
        print(f"  · {topic}: {len(state.focus_rules)} règle(s) {codes}")

    await run_event(state.clear_focus)
    assert state.has_focus is False, "Le focus doit pouvoir être retiré"

    await run_event(state.close_panel)
    assert state.is_open is False

    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())

"""Chargement serveur des panneaux CRM hors montage de composant.

Le montage (`on_mount`) n'est pas rejoué lors d'une navigation cliente ni lors
d'un accès direct par URL. La navigation charge donc elle-même le registre ou
l'espace tiers concerné : ce script vérifie que ce chargement fonctionne et que
le montage ne recharge pas ensuite ce qui est déjà en mémoire.
"""

import asyncio

from test_utils import run_event

from app.database import init_crm_tables, init_local_database
from app.seed_crm import seed_crm_if_empty
from app.states.crm_partners_state import CrmPartnersState
from app.states.crm_registers_state import CrmRegistersState


async def main() -> None:
    init_local_database()
    init_crm_tables()
    seed_crm_if_empty()

    # --- Registres : accès direct à /crm?vue=ventes --------------------
    registers = CrmRegistersState()
    await run_event(registers.enter_register_now, "ventes")
    assert registers.load_error == "", "Le registre des ventes ne doit pas échouer"
    assert registers.is_loading is False, "Le chargement doit être terminé"
    assert registers.register == "ventes"
    assert registers.loaded_register == "ventes"
    assert registers.rows, "Le registre des ventes doit contenir des pièces"
    ventes = len(registers.rows)

    # Le montage ne recharge pas un registre déjà chargé.
    await run_event(registers.enter_register, "ventes")
    assert len(registers.rows) == ventes, "Le montage ne doit pas vider le registre"

    # Changement de registre : filtres remis à zéro puis chargement.
    registers.search = "inexistant"
    registers.status_filter = "PAYEE"
    await run_event(registers.enter_register_now, "creances")
    assert registers.register == "creances"
    assert registers.search == "", "Le changement de registre vide la recherche"
    assert registers.status_filter == "", "Le changement de registre vide le statut"

    # --- Espaces tiers : accès direct à /crm?vue=clients ---------------
    partners = CrmPartnersState()
    await run_event(partners.enter_space_now, "clients")
    assert partners.space == "clients"
    assert partners.loaded_space == "clients"
    assert partners.partners, "L'espace clients doit contenir des tiers"
    assert partners.selected_id > 0, "Une fiche doit être sélectionnée"
    clients = len(partners.partners)

    # Le montage ne recharge pas un espace déjà chargé.
    await run_event(partners.enter_space, "clients")
    assert len(partners.partners) == clients, "Le montage ne doit pas vider la liste"

    # Changement d'espace : sélection et filtres remis à zéro.
    await run_event(partners.enter_space_now, "fournisseurs")
    assert partners.space == "fournisseurs"
    assert partners.loaded_space == "fournisseurs"
    assert partners.partners, "L'espace fournisseurs doit contenir des tiers"

    print(
        f"✓ Registres : {ventes} pièces en ventes ; espaces : {clients} clients, "
        f"{len(partners.partners)} fournisseurs"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())

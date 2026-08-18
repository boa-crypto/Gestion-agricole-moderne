"""État de l'administration des utilisateurs, rôles et permissions AgriPro."""

from __future__ import annotations

import datetime
from typing import TypedDict

import reflex as rx
from sqlalchemy import text

from app.access_control import (
    can_user,
    effective_permissions as user_permissions,
    expire_stale_delegations,
    log_activity,
    user_by_matricule,
    user_scope_summary,
)
from app.access_reference import (
    ACCESS_MODULES,
    FAMILY_LABELS,
    SCOPE_LABELS,
)
from app.exports import to_csv
from app.admin_operations import (
    AssignmentDetailRow,
    DelegationRow,
    OrgLevel,
    OrgNode,
    PersonalSummary,
    ResponsibilityRow,
    TaskRow,
    TeamMemberRow,
    complete_task,
    create_delegation,
    empty_node,
    empty_personal,
    load_assignment_filters,
    load_assignments,
    load_delegation_options,
    load_delegations,
    load_org_levels,
    load_org_node,
    load_pending_validations,
    load_personal_summary,
    load_responsibilities,
    load_tasks,
    load_team_members,
    revoke_delegation,
    validate_task,
)
from app.admin_users import (
    ActivityRow,
    AdminOverview,
    AssignmentRow,
    FunctionRow,
    Option,
    PermGroup,
    RbacRow,
    RoleRow,
    ScopeRow,
    TeamRow,
    UserDetail,
    UserRow,
    change_user_status,
    empty_detail,
    empty_overview,
    ensure_admin_data,
    load_activity,
    load_functions,
    load_journal,
    journal_kind_options,
    load_options,
    load_overview,
    load_rbac,
    load_teams,
    load_user_detail,
    load_users,
    today_label,
)

SECTIONS: list[tuple[str, str, str]] = [
    ("utilisateurs", "Utilisateurs", "users-round"),
    ("fonctions", "Fonctions agricoles", "briefcase"),
    ("equipes", "Équipes", "users"),
    ("permissions", "Rôles & permissions", "key-round"),
    ("organigramme", "Organigramme", "network"),
    ("espace", "Mon espace", "user-round"),
    ("workflows", "Validations", "check-check"),
    ("delegations", "Délégations", "hourglass"),
    ("affectations", "Affectations", "map"),
    ("journal", "Journal d'activité", "scroll-text"),
]

# Périmètres proposés à la création d'une permission temporaire.
SCOPE_CHOICES: list[tuple[str, str]] = [
    ("EXPLOITATION", SCOPE_LABELS["EXPLOITATION"]),
    ("SECTEUR", SCOPE_LABELS["SECTEUR"]),
    ("PARCELLE", SCOPE_LABELS["PARCELLE"]),
    ("EQUIPE", SCOPE_LABELS["EQUIPE"]),
    ("ACTIVITE", SCOPE_LABELS["ACTIVITE"]),
]

TABS: list[tuple[str, str, str]] = [
    ("profil", "Profil", "id-card"),
    ("organisation", "Organisation", "network"),
    ("roles", "Rôles & permissions", "shield-check"),
    ("perimetre", "Périmètre agricole", "map"),
    ("historique", "Historique", "history"),
]

# Statut cible → (verbe journalisé, action consignée dans le journal).
STATUS_EVENTS: dict[str, tuple[str, str]] = {
    "ACTIF": ("Réactivation", "ACTIVATE_USER"),
    "INACTIF": ("Désactivation", "DEACTIVATE_USER"),
    "SUSPENDU": ("Suspension", "SUSPEND_USER"),
    "ARCHIVE": ("Archivage", "ARCHIVE_USER"),
    "EN_ATTENTE": ("Mise en attente", "PENDING_USER"),
}


class RoleRegistryRow(TypedDict):
    id: int
    key: str
    label: str
    level: int
    icon: str
    color: str
    tagline: str
    users: int
    permissions: int


STATUS_BUTTONS: list[tuple[str, str, str]] = [
    ("REACTIVER", "Réactiver", "circle-check"),
    ("DESACTIVER", "Désactiver", "circle-pause"),
    ("SUSPENDRE", "Suspendre", "circle-slash"),
    ("ARCHIVER", "Archiver", "archive"),
]


class AdministrationState(rx.State):
    """Centre de gestion des personnes et des autorisations AgriPro."""

    is_loading: bool = True
    error: str = ""
    feedback: str = ""
    today: str = ""

    section: str = "utilisateurs"
    tab: str = "profil"

    actor_id: int = 0
    actor_label: str = "Propriétaire d'exploitation"

    kpis: AdminOverview = empty_overview()

    search: str = ""
    query: str = ""
    status_filter: str = "TOUS"
    role_filter: str = "TOUS"
    team_filter: str = "TOUTES"
    family_filter: str = "TOUTES"
    rbac_role: str = "chef-exploitation"
    form_key: int = 0

    status_options: list[Option] = []
    role_options: list[Option] = []
    team_options: list[Option] = []
    family_options: list[Option] = [
        {"value": key, "label": label} for key, label in FAMILY_LABELS.items()
    ]
    section_tabs: list[Option] = [
        {"value": key, "label": label} for key, label, _ in SECTIONS
    ]

    users: list[UserRow] = []
    selected_user_id: int = 0
    detail: UserDetail = empty_detail()
    detail_roles: list[RoleRow] = []
    detail_permissions: list[PermGroup] = []
    detail_scopes: list[ScopeRow] = []
    detail_assignments: list[AssignmentRow] = []
    detail_activity: list[ActivityRow] = []

    functions: list[FunctionRow] = []
    teams: list[TeamRow] = []
    roles: list[RoleRegistryRow] = []
    rbac: list[RbacRow] = []
    activity: list[ActivityRow] = []

    # --- Journal d'activité consultable et filtrable -------------------
    journal_kind: str = "TOUS"
    journal_module: str = "TOUS"
    journal_search: str = ""
    journal_sensitive_only: bool = False
    journal_kinds: list[Option] = journal_kind_options()
    journal_modules: list[Option] = [
        {"value": spec["key"], "label": spec["label"]}
        for spec in ACCESS_MODULES
    ]

    # Collections stables attendues par l'administration utilisateurs.
    effective_permissions: list[str] = []
    scope_parcels: list[int] = []

    # --- Organisation opérationnelle ---------------------------------
    org_levels: list[OrgLevel] = []
    org_selected_id: int = 0
    org_node: OrgNode = empty_node()

    personal_user_id: int = 0
    personal: PersonalSummary = empty_personal()
    personal_tasks: list[TaskRow] = []
    personal_team: list[TeamMemberRow] = []
    personal_responsibilities: list[ResponsibilityRow] = []

    pending_validations: list[TaskRow] = []
    # Alias stable et compatible : file d'attente des validations agricoles.
    validation_queue: list[TaskRow] = []
    open_tasks: list[TaskRow] = []

    delegations: list[DelegationRow] = []
    people_options: list[Option] = []
    delegable_roles: list[Option] = []
    delegation_teams: list[Option] = []
    delegation_error: str = ""

    assignments: list[AssignmentDetailRow] = []
    assignment_team_options: list[Option] = []
    assignment_activity_options: list[Option] = []
    assignment_team: str = "TOUTES"
    assignment_activity: str = "TOUTES"

    # ------------------------------------------------------------------
    # Vars dérivées
    # ------------------------------------------------------------------

    @rx.var
    def user_count(self) -> int:
        return len(self.users)

    @rx.var
    def visible_users(self) -> list[UserRow]:
        """Utilisateurs réellement affichés (alias stable de `users`)."""
        return self.users

    @rx.var
    def selected_user(self) -> UserDetail:
        """Fiche de l'utilisateur sélectionné (alias stable de `detail`)."""
        return self.detail

    @rx.var
    def permission_matrix(self) -> list[RbacRow]:
        """Matrice module × action du rôle courant (alias de `rbac`)."""
        return self.rbac

    @rx.var
    def role_count(self) -> int:
        return len(self.roles)

    @rx.var
    def has_selection(self) -> bool:
        return self.selected_user_id > 0

    @rx.var
    def coverage_label(self) -> str:
        total = self.kpis["users"]
        if total == 0:
            return "Aucun compte"
        return f"{self.kpis['active']} actifs sur {total} comptes"

    @rx.var
    def mfa_label(self) -> str:
        total = self.kpis["users"]
        if total == 0:
            return "MFA non configurée"
        share = int(round(100 * self.kpis["mfa"] / total))
        return f"{share} % des comptes protégés par MFA"

    @rx.var
    def rbac_role_label(self) -> str:
        for option in self.role_options:
            if option["value"] == self.rbac_role:
                return option["label"]
        return self.rbac_role

    @rx.var
    def rbac_granted(self) -> int:
        return sum(row["granted_count"] for row in self.rbac)

    @rx.var
    def pending_validation_count(self) -> int:
        return len(self.validation_queue)

    @rx.var
    def has_pending_validations(self) -> bool:
        return len(self.validation_queue) > 0

    @rx.var
    def active_delegation_count(self) -> int:
        return len([d for d in self.delegations if d["status"] == "ACTIVE"])

    @rx.var
    def journal_count(self) -> int:
        return len(self.activity)

    @rx.var
    def journal_sensitive_count(self) -> int:
        return len([item for item in self.activity if item["sensitive"]])

    @rx.var
    def journal_filter_label(self) -> str:
        pieces: list[str] = []
        if self.journal_kind != "TOUS":
            pieces.append(self.journal_kind)
        if self.journal_module != "TOUS":
            pieces.append(self.journal_module)
        if self.journal_sensitive_only:
            pieces.append("audit sensible")
        if self.journal_search.strip():
            pieces.append(f"« {self.journal_search.strip()} »")
        return " · ".join(pieces) if pieces else "Tout le journal"

    @rx.var
    def org_people_count(self) -> int:
        return sum(level["count"] for level in self.org_levels)

    # ------------------------------------------------------------------
    # Chargements
    # ------------------------------------------------------------------

    async def _refresh_users(self) -> None:
        self.users = await load_users(
            self.search, self.status_filter, self.role_filter, self.team_filter
        )
        if self.users and not any(
            item["id"] == self.selected_user_id for item in self.users
        ):
            self.selected_user_id = self.users[0]["id"]
        if not self.users:
            self.selected_user_id = 0
        await self._refresh_detail()

    async def _load_journal(self) -> None:
        """Recharge le journal d'activité en respectant les filtres courants."""
        self.activity = await load_journal(
            self.journal_kind,
            self.journal_module,
            self.journal_search,
            self.journal_sensitive_only,
            0,
            80,
        )

    async def _load_roles(self) -> None:
        """Registre des rôles applicatifs (effectif et volume de permissions)."""
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        """
                        SELECT r.id, r.key, r.label, COALESCE(r.level, 0),
                               COALESCE(r.icon, 'shield'),
                               COALESCE(r.color_hex, '#a3e635'),
                               COALESCE(r.tagline, ''),
                               (SELECT COUNT(*) FROM agripro_user_role ur
                                 WHERE ur.role_id = r.id),
                               (SELECT COUNT(*) FROM agripro_role_permission rp
                                 WHERE rp.role_id = r.id AND rp.is_granted = 1)
                        FROM agripro_role r
                        ORDER BY COALESCE(r.level, 0) DESC, r.label
                        """
                    )
                )
            ).all()
        self.roles = [
            {
                "id": int(row[0]),
                "key": str(row[1]),
                "label": str(row[2] or row[1]),
                "level": int(row[3] or 0),
                "icon": str(row[4]),
                "color": str(row[5]),
                "tagline": str(row[6]),
                "users": int(row[7] or 0),
                "permissions": int(row[8] or 0),
            }
            for row in rows
        ]

    async def _refresh_detail(self) -> None:
        if self.selected_user_id <= 0:
            self.detail = empty_detail()
            self.detail_roles = []
            self.detail_permissions = []
            self.detail_scopes = []
            self.detail_assignments = []
            self.detail_activity = []
            self.effective_permissions = []
            self.scope_parcels = []
            return
        (
            self.detail,
            self.detail_roles,
            self.detail_permissions,
            self.detail_scopes,
            self.detail_assignments,
        ) = await load_user_detail(self.selected_user_id)
        self.detail_activity = await load_activity(self.selected_user_id, 10)
        self.effective_permissions = await user_permissions(
            self.selected_user_id
        )
        summary = await user_scope_summary(self.selected_user_id)
        self.scope_parcels = [int(item) for item in summary["parcels"]]

    async def _sync_org_node(self, user_id: int) -> None:
        """Charge un nœud d'organigramme en gardant `id` synchronisé."""
        node = await load_org_node(int(user_id))
        node["id"] = int(user_id) if int(user_id) > 0 else int(node["id"])
        self.org_node = node
        self.org_selected_id = int(node["id"])

    async def _load_personal(self, user_id: int) -> None:
        """Espace personnel : synthèse, tâches, équipe et responsabilités."""
        if user_id <= 0:
            self.personal = empty_personal()
            self.personal_user_id = 0
            self.personal_tasks = []
            self.personal_team = []
            self.personal_responsibilities = []
            await self._load_workflows()
            return
        self.personal_user_id = int(user_id)
        summary = await load_personal_summary(user_id)
        summary["id"] = int(user_id)
        summary["user_id"] = int(user_id)
        self.personal = summary
        self.personal_tasks = await load_tasks(user_id, 24)
        self.personal_responsibilities = await load_responsibilities(user_id)
        async with rx.asession() as asession:
            team_id = int(
                (
                    await asession.execute(
                        text(
                            "SELECT COALESCE(team_id, 0) FROM agripro_user"
                            " WHERE id = :uid"
                        ),
                        {"uid": user_id},
                    )
                ).scalar()
                or 0
            )
        self.personal_team = await load_team_members(team_id)
        # La file de validation reflète l'espace personnel rechargé.
        await self._load_workflows()

    async def _load_workflows(self) -> None:
        """Validations en attente et chantiers ouverts de l'exploitation."""
        self.pending_validations = await load_pending_validations(0, 24)
        # `validation_queue` reste l'alias public, toujours synchronisé.
        self.validation_queue = list(self.pending_validations)
        tasks = await load_tasks(self.actor_id, 40)
        self.open_tasks = [
            task
            for task in tasks
            if task["status"] in ("PLANIFIEE", "EN_COURS")
        ][:12]

    async def _load_delegations(self) -> None:
        self.delegations = await load_delegations(40)
        (
            self.people_options,
            self.delegable_roles,
            self.delegation_teams,
        ) = await load_delegation_options()

    async def _load_assignments(self) -> None:
        self.assignments = await load_assignments(
            self.assignment_team, self.assignment_activity
        )

    async def _load_operations(self) -> None:
        """Charge l'ensemble de l'organisation opérationnelle."""
        self.org_levels = await load_org_levels()
        if self.org_selected_id <= 0:
            self.org_selected_id = self.actor_id or self.selected_user_id
        if self.org_selected_id <= 0 and self.org_levels:
            nodes = self.org_levels[0]["nodes"]
            if nodes:
                self.org_selected_id = int(nodes[0]["id"])
        await self._sync_org_node(self.org_selected_id)
        await self._load_personal(self.personal_user_id or self.org_selected_id)
        await self._load_workflows()
        await self._load_delegations()
        (
            self.assignment_team_options,
            self.assignment_activity_options,
        ) = await load_assignment_filters()
        await self._load_assignments()

    # ------------------------------------------------------------------
    # Organigramme, espace personnel, workflows et délégations
    # ------------------------------------------------------------------

    @rx.event
    async def select_org_node(self, user_id: int):
        """Sélectionne un nœud de l'organigramme et ouvre sa fiche."""
        self.org_selected_id = int(user_id)
        self.selected_user_id = int(user_id)
        self.is_loading = True
        yield
        await self._sync_org_node(int(user_id))
        await self._refresh_detail()
        self.is_loading = False

    @rx.event
    async def open_personal_space(self, user_id: int):
        """Ouvre l'espace personnel d'un profil utilisateur."""
        if int(user_id) <= 0:
            return
        self.section = "espace"
        self.is_loading = True
        yield
        await self._load_personal(int(user_id))
        self.is_loading = False

    @rx.event
    async def reload_personal_space(self):
        self.is_loading = True
        yield
        await self._load_personal(self.personal_user_id or self.actor_id)
        self.is_loading = False

    @rx.event
    async def reload_workflows(self):
        self.is_loading = True
        yield
        await self._load_workflows()
        self.is_loading = False

    @rx.event
    async def complete_intervention(self, intervention_id: int):
        """Clôture un chantier : Terminée, en attente de validation."""
        self.is_loading = True
        yield
        ok, message = await complete_task(self.actor_id, int(intervention_id))
        self.error = "" if ok else message
        self.feedback = message if ok else ""
        if ok:
            await self._load_workflows()
            await self._load_personal(self.personal_user_id or self.actor_id)
            self.activity = await load_activity(0, 18)
        self.is_loading = False
        yield rx.toast(message, duration=5000, close_button=True)

    @rx.event
    async def validate_intervention(self, intervention_id: int):
        """Valide une intervention terminée (workflow agricole)."""
        self.is_loading = True
        yield
        ok, message = await validate_task(self.actor_id, int(intervention_id))
        self.error = "" if ok else message
        self.feedback = message if ok else ""
        if ok:
            await self._load_workflows()
            await self._load_personal(self.personal_user_id or self.actor_id)
            self.kpis = await load_overview()
            self.activity = await load_activity(0, 18)
        self.is_loading = False
        yield rx.toast(message, duration=5000, close_button=True)

    @rx.event
    async def submit_delegation(self, form_data: dict):
        """Crée une permission temporaire bornée dans le temps."""
        self.delegation_error = ""

        def _int(key: str) -> int:
            raw = str(form_data.get(key, "") or "").strip()
            return int(raw) if raw.isdigit() else 0

        def _date(key: str) -> datetime.date | None:
            raw = str(form_data.get(key, "") or "").strip()
            if not raw:
                return None
            try:
                return datetime.date.fromisoformat(raw)
            except ValueError:
                return None

        self.is_loading = True
        yield
        ok, message = await create_delegation(
            self.actor_id,
            _int("delegator_id") or self.actor_id,
            _int("delegate_id"),
            _int("role_id"),
            form_data.get("scope_kindEXPLOITATION"),
            _int("team_id"),
            form_data.get("reason"),
            _date("start_date"),
            _date("end_date"),
        )
        self.delegation_error = "" if ok else message
        self.feedback = message if ok else ""
        if ok:
            self.form_key += 1
            await self._load_delegations()
            self.kpis = await load_overview()
            self.activity = await load_activity(0, 18)
            await self._refresh_detail()
        self.is_loading = False
        yield rx.toast(message, duration=5000, close_button=True)

    async def _delegation_candidates(self) -> tuple[int, int, int, int]:
        """(délégant, délégataire, rôle délégué, équipe) réalistes et actifs."""
        preferred = (
            self.personal_user_id
            or self.org_selected_id
            or self.selected_user_id
        )
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        """
                        SELECT u.id, COALESCE(u.role_id, 0),
                               COALESCE(u.team_id, 0), COALESCE(r.level, 0)
                        FROM agripro_user u
                        LEFT JOIN agripro_role r ON r.id = u.role_id
                        WHERE u.status = 'ACTIF'
                        ORDER BY COALESCE(r.level, 0) DESC, u.id
                        LIMIT 20
                        """
                    )
                )
            ).all()
        people = [
            (int(row[0]), int(row[1] or 0), int(row[2] or 0), int(row[3] or 0))
            for row in rows
        ]
        if len(people) < 2:
            return 0, 0, 0, 0
        delegator = next(
            (p for p in people if p[0] == int(preferred) and p[1] > 0),
            None,
        ) or next((p for p in people if p[1] > 0), people[0])
        delegate = next(
            (p for p in people if p[0] != delegator[0]),
            people[0],
        )
        return delegator[0], delegate[0], delegator[1], delegator[2]

    @rx.event
    async def create_temporary_delegation(self):
        """Crée une permission temporaire réaliste depuis le profil courant.

        Le délégant est le profil sélectionné (ou le premier responsable actif)
        et le délégataire le premier autre collaborateur actif. L'opération est
        contrôlée côté serveur, idempotente (une seule délégation ouverte pour
        ce couple et ce motif) et journalisée sous `CREATE_DELEGATION`.
        """
        self.delegation_error = ""
        self.is_loading = True
        yield
        (
            delegator,
            delegate,
            role_id,
            team_id,
        ) = await self._delegation_candidates()
        if delegator <= 0 or delegate <= 0 or role_id <= 0:
            self.is_loading = False
            self.delegation_error = (
                "Aucun couple délégant / délégataire disponible."
            )
            yield rx.toast(self.delegation_error, duration=4000)
            return

        reason = "Absence du responsable : continuité de service AgriPro."
        today = datetime.date.today()
        end = today + datetime.timedelta(days=7)

        async with rx.asession() as asession:
            existing = int(
                (
                    await asession.execute(
                        text(
                            """
                            SELECT COALESCE(MAX(id), 0)
                            FROM agripro_delegation
                            WHERE delegator_id = :did AND delegate_id = :tid
                              AND COALESCE(role_id, 0) = :rid
                              AND COALESCE(reason, '') = :reason
                              AND status IN ('ACTIVE', 'PLANIFIEE')
                            """
                        ),
                        {
                            "did": delegator,
                            "tid": delegate,
                            "rid": role_id,
                            "reason": reason,
                        },
                    )
                ).scalar()
                or 0
            )

        if existing > 0:
            await self._load_delegations()
            self.is_loading = False
            message = "Une permission temporaire identique est déjà active."
            self.feedback = message
            yield rx.toast(message, duration=4000, close_button=True)
            return

        ok, message = await create_delegation(
            self.actor_id,
            delegator,
            delegate,
            role_id,
            "EQUIPE" if team_id > 0 else "EXPLOITATION",
            team_id,
            reason,
            today,
            end,
        )
        self.delegation_error = "" if ok else message
        self.feedback = message if ok else ""
        if ok:
            await log_activity(
                self.actor_id,
                "DELEGATION",
                module="utilisateurs",
                action="CREATE_DELEGATION",
                object_type="DELEGATION",
                object_ref=str(delegate),
                object_id=delegate,
                summary=(
                    f"Permission temporaire accordée du "
                    f"{today.isoformat()} au {end.isoformat()} ({reason})"
                ),
                team_id=team_id,
                is_sensitive=True,
            )
            await self._load_delegations()
            self.kpis = await load_overview()
            self.activity = await load_activity(0, 18)
            await self._refresh_detail()
        self.is_loading = False
        yield rx.toast(message, duration=5000, close_button=True)

    @rx.event
    async def expire_delegation(self, delegation_id: int):
        """Met fin immédiatement à une permission temporaire et la journalise."""
        self.is_loading = True
        yield
        ok, message = await revoke_delegation(self.actor_id, int(delegation_id))
        self.delegation_error = "" if ok else message
        self.feedback = message if ok else ""
        if ok:
            await log_activity(
                self.actor_id,
                "DELEGATION",
                module="utilisateurs",
                action="EXPIRE_DELEGATION",
                object_type="DELEGATION",
                object_ref=str(delegation_id),
                object_id=int(delegation_id),
                summary=(
                    "Fin anticipée d'une permission temporaire "
                    f"(délégation {int(delegation_id)})."
                ),
                is_sensitive=True,
            )
            await self._load_delegations()
            self.kpis = await load_overview()
            self.activity = await load_activity(0, 18)
        self.is_loading = False
        yield rx.toast(message, duration=5000, close_button=True)

    @rx.event
    async def revoke_temporary_permission(self, delegation_id: int):
        self.is_loading = True
        yield
        ok, message = await revoke_delegation(self.actor_id, int(delegation_id))
        self.delegation_error = "" if ok else message
        self.feedback = message if ok else ""
        if ok:
            await self._load_delegations()
            self.kpis = await load_overview()
            self.activity = await load_activity(0, 18)
        self.is_loading = False
        yield rx.toast(message, duration=5000, close_button=True)

    @rx.event
    async def expire_temporary_permissions(self):
        """Passe en expiré ce qui a dépassé sa date de fin, et journalise."""
        self.is_loading = True
        yield
        closed = await expire_stale_delegations()
        await self._load_delegations()
        self.kpis = await load_overview()
        if closed > 0:
            await log_activity(
                self.actor_id,
                "DELEGATION",
                module="utilisateurs",
                action="CLOTURER",
                object_type="DELEGATION",
                object_ref="expiration-automatique",
                summary=(
                    f"{closed} permission(s) temporaire(s) arrivée(s) à "
                    "échéance ont été retirées."
                ),
                is_sensitive=True,
            )
            self.activity = await load_activity(0, 18)
        self.is_loading = False
        message = (
            f"{closed} délégation(s) expirée(s)."
            if closed > 0
            else "Aucune délégation à expirer."
        )
        yield rx.toast(message, duration=4000, close_button=True)

    @rx.event
    async def set_assignment_team(self, value: str):
        self.assignment_team = value
        self.is_loading = True
        yield
        await self._load_assignments()
        self.is_loading = False

    @rx.event
    async def set_assignment_activity(self, value: str):
        self.assignment_activity = value
        self.is_loading = True
        yield
        await self._load_assignments()
        self.is_loading = False

    @rx.event
    async def reset_assignment_filters(self):
        self.assignment_team = "TOUTES"
        self.assignment_activity = "TOUTES"
        self.form_key += 1
        self.is_loading = True
        yield
        await self._load_assignments()
        self.is_loading = False

    @rx.event
    async def load_administration(self):
        self.is_loading = True
        self.error = ""
        yield
        await ensure_admin_data()
        self.today = await today_label()
        self.actor_id = await user_by_matricule("U001")
        self.kpis = await load_overview()
        (
            self.status_options,
            self.role_options,
            self.team_options,
        ) = await load_options()
        self.functions = await load_functions(self.family_filter)
        self.teams = await load_teams()
        await self._load_roles()
        self.rbac = await load_rbac(self.rbac_role)
        await self._load_journal()
        await self._refresh_users()
        await self._load_operations()
        self.is_loading = False

    @rx.event
    async def set_journal_kind(self, value: str):
        self.journal_kind = value
        self.is_loading = True
        yield
        await self._load_journal()
        self.is_loading = False

    @rx.event
    async def set_journal_module(self, value: str):
        self.journal_module = value
        self.is_loading = True
        yield
        await self._load_journal()
        self.is_loading = False

    @rx.event
    async def set_journal_search(self, value: str):
        self.journal_search = value
        self.is_loading = True
        yield
        await self._load_journal()
        self.is_loading = False

    @rx.event
    async def toggle_journal_sensitive(self):
        self.journal_sensitive_only = not self.journal_sensitive_only
        self.is_loading = True
        yield
        await self._load_journal()
        self.is_loading = False

    @rx.event
    async def set_journal_sensitive_only(self, value: bool | str):
        """Filtre « audit sensible » : nom stable attendu par l'intégration.

        Accepte un booléen ou la valeur textuelle d'un contrôle de formulaire
        (`"true"`, `"1"`, `"on"`) puis recharge le journal filtré depuis
        `agripro_activity_log`.
        """
        if isinstance(value, bool):
            wanted = value
        else:
            wanted = str(value).strip().lower() in ("true", "1", "on", "oui")
        self.journal_sensitive_only = wanted
        self.is_loading = True
        yield
        await self._load_journal()
        self.is_loading = False

    @rx.event
    async def reset_journal_filters(self):
        self.journal_kind = "TOUS"
        self.journal_module = "TOUS"
        self.journal_search = ""
        self.journal_sensitive_only = False
        self.form_key += 1
        self.is_loading = True
        yield
        await self._load_journal()
        self.is_loading = False

    # ------------------------------------------------------------------
    # Exports simples des listes visibles
    # ------------------------------------------------------------------

    @rx.event
    def export_users(self):
        """Exporte le registre filtré des utilisateurs au format CSV."""
        content = to_csv(
            [
                "Matricule",
                "Nom",
                "Fonction",
                "Rôle",
                "Équipe",
                "Secteur",
                "Statut",
                "MFA",
                "Périmètres",
                "Affectations",
                "Dernière connexion",
            ],
            [
                [
                    user["matricule"],
                    user["name"],
                    user["function_label"],
                    user["role_label"],
                    user["team_label"],
                    user["sector"],
                    user["status_label"],
                    user["mfa_label"],
                    user["scopes"],
                    user["assignments"],
                    user["last_login"],
                ]
                for user in self.users
            ],
        )
        return rx.download(data=content, filename="agripro-utilisateurs.csv")

    @rx.event
    def export_journal(self):
        """Exporte le journal d'activité tel qu'il est filtré à l'écran."""
        content = to_csv(
            [
                "Date",
                "Acteur",
                "Type",
                "Module",
                "Action",
                "Objet",
                "Résumé",
                "Audit sensible",
            ],
            [
                [
                    item["when"],
                    item["actor"],
                    item["kind_label"],
                    item["module_label"],
                    item["action_label"],
                    item["object_ref"],
                    item["summary"],
                    "oui" if item["sensitive"] else "non",
                ]
                for item in self.activity
            ],
        )
        return rx.download(data=content, filename="agripro-journal.csv")

    @rx.event
    def export_assignments(self):
        """Exporte les affectations parcelles / cultures / équipes visibles."""
        content = to_csv(
            [
                "Collaborateur",
                "Rôle",
                "Parcelle",
                "Culture",
                "Équipe",
                "Activité",
                "Secteur",
                "Campagne",
                "Responsable",
                "Période",
            ],
            [
                [
                    item["user_label"],
                    item["role_label"],
                    item["parcel"],
                    item["crop"],
                    item["team"],
                    item["activity"],
                    item["sector"],
                    item["season"],
                    "oui" if item["responsible"] else "non",
                    item["period"],
                ]
                for item in self.assignments
            ],
        )
        return rx.download(data=content, filename="agripro-affectations.csv")

    @rx.event
    def set_section(self, value: str):
        self.section = value

    @rx.event
    def set_tab(self, value: str):
        self.tab = value

    @rx.event
    async def select_user(self, user_id: int):
        self.selected_user_id = user_id
        self.tab = "profil"
        self.is_loading = True
        yield
        await self._refresh_detail()
        self.is_loading = False

    @rx.event
    async def set_search(self, value: str):
        self.search = value
        self.query = value
        self.is_loading = True
        yield
        await self._refresh_users()
        self.is_loading = False

    @rx.event
    async def set_query(self, value: str):
        """Alias de recherche attendu par l'administration utilisateurs."""
        self.query = value
        self.search = value
        self.is_loading = True
        yield
        await self._refresh_users()
        self.is_loading = False

    @rx.event
    async def set_status_filter(self, value: str):
        self.status_filter = value
        self.is_loading = True
        yield
        await self._refresh_users()
        self.is_loading = False

    @rx.event
    async def set_role_filter(self, value: str):
        self.role_filter = value
        self.is_loading = True
        yield
        await self._refresh_users()
        self.is_loading = False

    @rx.event
    async def set_team_filter(self, value: str):
        self.team_filter = value
        self.is_loading = True
        yield
        await self._refresh_users()
        self.is_loading = False

    @rx.event
    async def reset_filters(self):
        self.search = ""
        self.query = ""
        self.status_filter = "TOUS"
        self.role_filter = "TOUS"
        self.team_filter = "TOUTES"
        self.form_key += 1
        self.is_loading = True
        yield
        await self._refresh_users()
        self.is_loading = False

    @rx.event
    async def set_family_filter(self, value: str):
        self.family_filter = value
        self.is_loading = True
        yield
        self.functions = await load_functions(value)
        self.is_loading = False

    @rx.event
    async def set_rbac_role(self, value: str):
        self.rbac_role = value
        self.is_loading = True
        yield
        self.rbac = await load_rbac(value)
        self.is_loading = False

    @rx.event
    async def set_user_status(self, user_id: int, status: str):
        """Applique un statut à un utilisateur et journalise le changement."""
        target = str(status or "").strip().upper()
        if target not in STATUS_EVENTS:
            self.error = "Statut utilisateur inconnu."
            return
        if int(user_id) <= 0:
            self.error = "Sélectionnez d'abord un utilisateur."
            return

        self.is_loading = True
        yield
        # Contrôle serveur systématique : le frontend n'est jamais une protection.
        decision = await can_user(
            self.actor_id,
            "utilisateurs",
            "MODIFIER",
            object_type="UTILISATEUR",
            object_ref=str(int(user_id)),
        )
        if not decision.allowed:
            self.is_loading = False
            self.error = decision.message
            yield rx.toast(decision.message, duration=5000, close_button=True)
            return
        if int(user_id) == self.actor_id:
            self.is_loading = False
            self.error = "Vous ne pouvez pas modifier votre propre compte."
            yield rx.toast(self.error, duration=4000, close_button=True)
            return
        verb, action = STATUS_EVENTS[target]
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT matricule, first_name || ' ' || last_name, status
                        FROM app_user WHERE id = :uid
                        """
                    ),
                    {"uid": int(user_id)},
                )
            ).first()
            if row is None:
                self.is_loading = False
                self.error = "Utilisateur introuvable."
                return
            matricule = str(row[0])
            full_name = str(row[1]).strip()
            previous = str(row[2])
            await asession.execute(
                text("UPDATE app_user SET status = :s WHERE id = :uid"),
                {"s": target, "uid": int(user_id)},
            )
            await asession.commit()

        await log_activity(
            self.actor_id,
            "MODIFICATION",
            module="utilisateurs",
            action=action,
            object_type="UTILISATEUR",
            object_ref=matricule,
            object_id=int(user_id),
            summary=(
                f"{verb} du compte {full_name} ({matricule}) : "
                f"{previous} → {target}."
            ),
            scope_label="Toute l'exploitation",
            is_sensitive=True,
        )

        self.selected_user_id = int(user_id)
        self.error = ""
        self.feedback = f"{verb} : {full_name}."
        self.kpis = await load_overview()
        await self._load_journal()
        await self._refresh_users()
        await self._refresh_detail()
        self.is_loading = False
        yield rx.toast(self.feedback, duration=4000, close_button=True)

    @rx.event
    async def apply_status(self, action: str):
        self.is_loading = True
        yield
        allowed, message = await change_user_status(
            self.actor_id, self.selected_user_id, action
        )
        self.feedback = message if allowed else ""
        self.error = "" if allowed else message
        if allowed:
            self.kpis = await load_overview()
            self.activity = await load_activity(0, 18)
            await self._refresh_users()
        self.is_loading = False
        yield rx.toast(
            message,
            duration=5000,
            close_button=True,
        )

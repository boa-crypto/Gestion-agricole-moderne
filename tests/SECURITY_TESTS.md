# Régressions d'autorisation AgriPro

La suite `tests.test_server_guard` utilise uniquement un fichier SQLite temporaire pour les comptes, sessions et règles de menu. Elle remplace la lecture des rôles locaux ; elle ne se connecte pas à la base de menu déployée et ne lance aucune migration métier.

Exécuter avec Python unittest les modules suivants : `tests.test_server_guard`, `tests.test_auth_entry`, `tests.test_menu_policy`, `tests.test_menu_policy_admin`, `tests.test_navigation`, `tests.test_menu_configuration`, `tests.test_menu_session_errors`.

Les anciens scripts métier qui appellent directement des opérations privilégiées sans session ne constituent plus des parcours autorisés. Les fonctions Python protégées exigent un contexte d'événement vérifié ; les tests de validation pure doivent appeler les validateurs purs, et les tests d'intégration doivent passer par les gestionnaires protégés avec une session isolée. Ne pas ajouter de mode de contournement en production pour ces scripts.

La couverture inventorie toutes les classes d'état métier importées et leurs événements publics, y compris les setters enregistrés. L'installation est idempotente et précède les pages. Une classe métier non répertoriée bloque l'installation plutôt que de bénéficier d'un accès implicite.

Les lectures transversales qui exposent plusieurs domaines (recherche globale, diagnostic, fiches CRM 360°, options de factures) exigent les droits de consultation de tous les domaines lus. Les autorisations d'une destination ne donnent jamais automatiquement les droits d'un autre domaine présent sur la même page. Un chargeur facultatif refusé peut être sauté dans la chaîne existante, sans exécuter son code métier.

Aucun nouvel endpoint HTTP n'est ajouté. Les API phénologiques existantes sont des fonctions Python, désormais contrôlées. Les validations métier locales restent des contrôles supplémentaires et ne remplacent pas la vérification durable de session.

Ces tests ont été ajoutés sans exécution dans cette session d'édition, qui ne fournit pas de terminal. Les résultats d'exécution ne sont donc pas attestés ici.

# Captures — smile_dynamic_action_visibility (Odoo 20.0)

Prises avec Playwright (Chromium headless, 1400x700) par `playwright_scenario.js`,
sur une base `base,web` + ce module, utilisateur admin.

Données de test :

- partenaires : « Alpha SA » (société : TVA `BE0477472701`, email), « Bob Martin » (email), « Carla Dupont » (sans email) ;
- rapport « Partner Sheet » (`ir.actions.report`) lié à `res.partner` (list, form) ;
- règle « No merge on companies » : action *Merge*, condition `record.is_company` ;
- règle « Partner sheet only with email » : rapport *Partner Sheet*, condition `not record.email`.

En 20.0, `is_company` est calculé (entité commerciale propre + TVA renseignée) : une société sans TVA n'est pas `is_company`.

| Capture | Cas | Attendu |
|---|---|---|
| 01_rules_list.png | Liste des règles (Paramètres > Technique > Action Rules) | — |
| 02_rule_form.png | Formulaire d'une règle | — |
| 03_person_selected_merge_visible.png | Liste, Bob sélectionné, menu Actions | *Merge* visible |
| 04_company_added_merge_hidden.png | Ajout d'Alpha SA à la sélection | *Merge* masqué (un enregistrement suffit) |
| 05_company_removed_merge_back.png | Alpha SA retiré de la sélection | *Merge* de nouveau visible |
| 06_print_with_email_visible.png | Bob sélectionné, menu Imprimer | *Partner Sheet* visible |
| 07_print_without_email_hidden.png | Carla sélectionnée, menu Imprimer | *Partner Sheet* masqué |
| 08_form_with_email_report_visible.png | Formulaire de Bob, menu engrenage | *Partner Sheet* visible |
| 09_form_next_record_report_hidden.png | Pager vers Carla, menu engrenage | *Partner Sheet* masqué |

Relancer : `node playwright_scenario.js <dossier_de_sortie>` (paquet npm `playwright`, Odoo sur `localhost:8069`,
lancé avec `--http-interface=0.0.0.0`, login admin/admin).

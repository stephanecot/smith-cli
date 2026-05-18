MCP:
??

=> simplifier config => pas besoin de tous les details


On va développer le skill /smith-new-project <description>
  edit:
       décrire un peu plus le agent.MD
       adapter le format du raport

  current:
  -> pour initier un nouveau projet
    Ce skill, va déclancher un worklow.
      1) lancement de /smith-init (uniquement si le fichier .smith/smith.config n'existe pas
      2) L'agent va poser des questions par rapport aux stack techniques si rien n'a été précisé dans la <description>
      3) Utilisation du skill /smith-architecture-format pour créer le fichier associé en rapport avec les questions posés
      4) On va recuper les bundle associés par rapport à la config du projet.
         Par rapport au provider IA utilisé, il faudra générer les bon fichiers au final
         on utilisera le skill /smith-bundle-install pour ça
         Important: Pour chaque bundle, on utilisera un sous agent dédié
      5) On va recuperer les templates associés par rapport à la config du projet.
        Par rapport au provider IA utilisé, il faudra générer les bon fichiers aufinal
        On utilisera le skill /smith-template-install pour ca
        Important: Pour chaque template, on utilisera un sous agent dédié
      6) On génére le fichier AGENTS.md qui décrira les bases du projet (100 lignes max)
      7) Utilisation du skill /smith-config-format pour créer le fichier associé en rapport les bundle et template installés
      8) Déclanchement d'un sous agent dédié à la vérification complete de tout ce qui a été fait
      9) Génération d'un rapport .md dans .smith/report/ pour indiquer tout ce qui a été fait.
          Créé un skill dédié pour ça avec un template
       => ajout de la génération de doc


/smith-convert-project
  -> pour convertir un projet existant
    lancement de /smith-init (uniquement si le fichier .smith/smith.config n'existe pas
    création de la doc
    Mise en place de la config
    recupération des bon templates / bundle


Exemple de prompt:
- je veux un projet java / Spring Boot -> install moi tout ce dont j'ai besoin pour ca.
  - init du projet
  - recupereation des bons  "template"
  - récupération des bon bundle


Smith skills:
- skill pour te proposer les bon bundles

bundle:
- angular init
- spring int
--> utilise les templates

sdlc:
- /plan
  /feature
  /fixe
  /explain
=> Notion de template à prendre en compte

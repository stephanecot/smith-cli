# {{project_name}} — Functional specification

<!--
  MACRO TEMPLATE — filled by `smith-functional-doc-writer` during
  `/smith-generate-docs`. Each `{{placeholder}}` is substituted by the
  agent with content derived from the project. Section headers are
  fixed ; the agent never invents new top-level sections, never removes
  existing ones. Missing content → "_Not applicable_".
-->

## 1. Mission

{{mission_paragraph}}

## 2. Personas

{{personas_list}}

<!--
  Each persona is a `- {{role}} — {{what they need from the system}}` bullet.
  Pick 3–6 personas ; one of them MUST be a system admin / operator persona
  even if the rest are end-users.
-->

## 3. User stories

{{user_stories_by_feature}}

<!--
  Group user stories by feature heading (`### {{Feature}}`). Each story is :
    - As a {{role}}, I want {{capability}}, so that {{outcome}}.
  Every story MUST name a measurable outcome ; vague ones get an
  `[INFERRED]` marker.
-->

## 4. Business rules

{{business_rules_list}}

<!--
  One bullet per rule. Cite a real constraint (validation, state
  transition, RBAC, money / time handling). Mark unverifiable rules with
  `[INFERRED]` at the end of the bullet.
-->

## 5. Integrations

{{integrations_list}}

<!--
  One bullet per external system : `- {{system}} — {{purpose}} — {{auth model}}`.
  If the project has no integrations, write `_Not applicable_`.
-->

## 6. Out of scope

{{out_of_scope_list}}

<!--
  Anchor expectations : what the system intentionally does NOT do.
  Helps reviewers spot misaligned feature requests later.
-->

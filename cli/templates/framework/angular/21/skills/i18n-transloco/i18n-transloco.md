
# Skill — i18n with Transloco

Transloco 8.x. Default `fr`, fallback `en`.

## Files

- `frontend/transloco.config.ts` — declares langs, default, root translations path.
- `frontend/src/app/app.config.ts` — `provideTransloco({ availableLangs, defaultLang, fallbackLang, reRenderOnLangChange })`.
- `frontend/src/app/transloco-loader.ts` — HTTP loader fetching `public/i18n/{lang}.json`.
- `frontend/public/i18n/fr.json` — French (source of truth).
- `frontend/public/i18n/en.json` — English (parity required).

## Iron rule — no hardcoded text

- **Every** user-visible string in templates and components goes through Transloco. Never `<button>Save</button>`. Always `<button>{{ 'common.save' | transloco }}</button>`.
- Toaster messages, validation errors, confirmation dialogs — all keyed.
- Backend error envelopes carry an error `code`; the frontend resolves a key (`errors.<code>`) — never displays raw backend strings.

## Key naming convention

`<feature>.<section>.<element>` — kebab-case for multi-word segments.

- `common.actions.save`, `common.actions.cancel`, `common.actions.delete`
- `common.feedback.success`, `common.feedback.error`
- `users.list.title`, `users.list.empty`, `users.form.email-label`, `users.form.email-required`
- `workspaces.detail.members.invite-button`
- `errors.unauthorized`, `errors.network`, `errors.unknown`
- `validation.required`, `validation.email`, `validation.min-length`

Reuse keys when wording is identical across screens. Don't create `users.save` and `workspaces.save` — use `common.actions.save`.

## Translation file structure

Both `fr.json` and `en.json` use a nested object matching the dotted key hierarchy:

```json
{
  "common": { "actions": { "save": "Enregistrer", "cancel": "Annuler" } },
  "users":  { "list":    { "title": "Utilisateurs", "empty": "Aucun utilisateur" } }
}
```

**Parity is mandatory**: every key in `fr.json` exists in `en.json` and vice-versa. CI fails on diverging key sets.

## Template usage

```html
<h1>{{ 'users.list.title' | transloco }}</h1>

<ng-container *transloco="let t">
  <h1>{{ t('users.list.title') }}</h1>
  <p>{{ t('users.list.subtitle', { count: total() }) }}</p>
</ng-container>
```

Interpolation in JSON: `{ "users.list.subtitle": "{{count}} utilisateur(s)" }`.

## Component usage

```typescript
import { inject } from '@angular/core';
import { TranslocoService } from '@jsverse/transloco';

@Component({ /* ... */ })
export class FooComponent {
  private readonly i18n = inject(TranslocoService);

  showWelcome(name: string): string {
    return this.i18n.translate('users.welcome', { name });
  }

  switchLanguage(lang: 'fr' | 'en'): void {
    this.i18n.setActiveLang(lang);
  }
}
```

In tests, prefer `getTranslocoModule()` from the testing harness or stub `TranslocoService`.

## Forbidden

- Hardcoded user-visible strings in `.html` or `.ts`.
- Concatenating translated fragments to build sentences (`{{ 'a' | transloco }} {{ 'b' | transloco }}`). Build the full sentence as one key with parameters.
- Translating proper nouns or trademarks unless specifically required.
- Missing key in either locale file. Both must be in sync.
- Calling `translate()` in the constructor — translations may not be loaded yet. Use `selectTranslate()` (observable) or `langChanges$`.

## Adding a new key — checklist

1. Pick a key following the convention.
2. Add it to `fr.json` (the design language) **and** `en.json`.
3. Use it in the template/component.
4. Add a unit test asserting the translated text renders (Transloco test harness).
5. Run `npm test` — coverage must remain ≥ 80%.

## Language switcher (UX standard)

A single design-system `LangSwitcherComponent` lives in `design-system/` and is imported anywhere the user can change language. **Never** re-implement language switching in features.

## Validation gate

```bash
cd frontend
npm test -- --run
npm run i18n:check            # diffs key sets between fr.json and en.json
```

If `i18n:check` doesn't exist yet, the agent adds it as a Node script under `frontend/scripts/i18n-check.mjs` and wires it to `package.json`.

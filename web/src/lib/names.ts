// Species common names in the visitor's language. The LanguageProvider loads the
// names once and remounts the page when the language changes, so plain function
// calls like displayName() pick up the new language without hooks.

export type SpeciesNames = Record<string, Record<string, string>>;

let names: SpeciesNames = {};
let lang = "en";

export function setSpeciesNames(next: SpeciesNames, nextLang: string) {
  names = next;
  lang = nextLang;
}

export function currentLanguage() {
  return lang;
}

export function localName(species: string): string | undefined {
  const name = names[species]?.[lang];
  // Some languages (e.g. Norwegian) write bird names in lower case.
  return name ? name.charAt(0).toLocaleUpperCase(lang) + name.slice(1) : undefined;
}

export function languageLabel(code: string) {
  try {
    const label = new Intl.DisplayNames([code], { type: "language" }).of(code) ?? code;
    return label.charAt(0).toLocaleUpperCase(code) + label.slice(1);
  } catch {
    return code.toUpperCase();
  }
}

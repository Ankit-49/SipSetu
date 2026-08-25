import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";

import en from "./locales/en.json";
import hi from "./locales/hi.json";

export const SUPPORTED_LOCALES = [
  { code: "en", nativeName: "English", englishName: "English" },
  { code: "hi", nativeName: "हिन्दी", englishName: "Hindi" },
];

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      hi: { translation: hi },
    },
    fallbackLng: "en",
    debug: false,
    interpolation: {
      escapeValue: false, // React already escapes
    },
    detection: {
      order: [
        "localStorage",
        "querystring",
        "navigator",
        "htmlTag",
      ],
      lookupLocalStorage: "sipsetu_locale",
      lookupQuerystring: "lang",
      caches: ["localStorage"],
    },
  });

export default i18n;

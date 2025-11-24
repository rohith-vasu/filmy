export const GENRES = [
    "Action", "Adventure", "Animation", "Comedy", "Crime",
    "Documentary", "Drama", "Family", "Fantasy", "History",
    "Horror", "Music", "Mystery", "Romance", "Science Fiction",
    "TV Movie", "Thriller", "War", "Western"
];

export const LANGUAGES = {
    "en": "English",
    "ko": "Korean",
    "fr": "French",
    "ja": "Japanese",
    "it": "Italian",
    "es": "Spanish",
    "pl": "Polish",
    "pt": "Portuguese",
    "hi": "Hindi",
    "da": "Danish",
    "de": "German",
    "cn": "Cantonese",
    "id": "Indonesian",
    "zh": "Mandarin",
    "sv": "Swedish",
    "th": "Thai",
    "fi": "Finnish",
    "te": "Telugu",
    "nl": "Dutch",
    "et": "Estonian",
    "bn": "Bengali",
    "cs": "Czech",
    "ml": "Malayalam",
    "ta": "Tamil",
    "kn": "Kannada",
    "vi": "Vietnamese",
    "sk": "Slovak",
    "lv": "Latvian",
    "sl": "Slovenian",
    "mr": "Marathi",
    "hr": "Croatian",
    "or": "Oriya"
};

export const LANGUAGE_OPTIONS = Object.values(LANGUAGES)
    .sort((a, b) => a.localeCompare(b))
    .map((label) => ({ value: label, label }));

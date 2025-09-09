/**
 * Localization System for Multi-language Support
 * Supports French, Arabic, and English with RTL support
 */

class LocalizationSystem {
    constructor() {
        this.currentLanguage = 'ar'; // Default language
        this.translations = {};
        this.rtlLanguages = ['ar'];
        this.isRTL = false;

        // Initialize the system
        this.init();
    }

    /**
     * Initialize the localization system
     */
    async init() {
        // Load default language
        await this.loadLanguage(this.currentLanguage);

        // Apply initial translations
        this.applyTranslations();

        // Set up language switching
        this.setupLanguageSwitching();

        // Set initial direction
        this.updateDirection();
    }

    /**
     * Load language file
     * @param {string} lang - Language code (fr, ar, en)
     */
    async loadLanguage(lang) {
        try {
            const response = await fetch(`/static/locales/${lang}.json`);
            if (!response.ok) {
                throw new Error(`Failed to load language file: ${lang}`);
            }
            this.translations[lang] = await response.json();
            console.log(`✅ Language loaded: ${lang}`);
        } catch (error) {
            console.error(`❌ Error loading language ${lang}:`, error);
            // Fallback to French if loading fails
            if (lang !== 'fr') {
                await this.loadLanguage('fr');
            }
        }
    }

    /**
     * Switch to a different language
     * @param {string} lang - Language code (fr, ar, en)
     */
    async switchLanguage(lang) {
        if (this.currentLanguage === lang) return;

        // Load language if not already loaded
        if (!this.translations[lang]) {
            await this.loadLanguage(lang);
        }

        this.currentLanguage = lang;
        this.isRTL = this.rtlLanguages.includes(lang);

        // Update UI
        this.updateDirection();
        this.applyTranslations();
        this.updateLanguageSelector();

        // Update document language and direction
        document.documentElement.lang = lang;
        document.documentElement.dir = this.isRTL ? 'rtl' : 'ltr';

        // Store preference
        localStorage.setItem('preferredLanguage', lang);

        // Dispatch language change event
        window.dispatchEvent(new CustomEvent('languageChanged', {
            detail: { language: lang, isRTL: this.isRTL }
        }));

        console.log(`🌐 Language switched to: ${lang}`);
    }

    /**
     * Get translation for a key
     * @param {string} key - Translation key (e.g., 'navigation.home')
     * @param {object} params - Parameters for interpolation
     * @returns {string} Translated text
     */
    t(key, params = {}) {
        const translation = this.getNestedValue(this.translations[this.currentLanguage], key);

        if (!translation) {
            console.warn(`⚠️ Translation missing for key: ${key}`);
            return key; // Return key as fallback
        }

        // Handle interpolation
        return this.interpolate(translation, params);
    }

    /**
     * Get nested value from object using dot notation
     * @param {object} obj - Object to search
     * @param {string} path - Dot notation path
     * @returns {any} Value at path
     */
    getNestedValue(obj, path) {
        return path.split('.').reduce((current, key) => {
            return current && current[key] !== undefined ? current[key] : null;
        }, obj);
    }

    /**
     * Interpolate parameters into translation string
     * @param {string} text - Text with placeholders
     * @param {object} params - Parameters to interpolate
     * @returns {string} Interpolated text
     */
    interpolate(text, params) {
        return text.replace(/\{\{(\w+)\}\}/g, (match, key) => {
            return params[key] !== undefined ? params[key] : match;
        });
    }

    /**
     * Apply translations to all elements with data-i18n attribute
     */
    applyTranslations() {
        const elements = document.querySelectorAll('[data-i18n]');

        elements.forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.t(key);

            if (translation) {
                // Handle different element types
                if (element.tagName === 'INPUT' && element.type === 'text') {
                    element.placeholder = translation;
                } else if (element.tagName === 'INPUT' && element.type === 'submit') {
                    element.value = translation;
                } else {
                    element.textContent = translation;
                }
            }
        });
    }

    /**
     * Update text direction based on current language
     */
    updateDirection() {
        const body = document.body;

        if (this.isRTL) {
            body.classList.add('rtl');
            body.classList.remove('ltr');
        } else {
            body.classList.add('ltr');
            body.classList.remove('rtl');
        }
    }

    /**
     * Update language selector UI
     */
    updateLanguageSelector() {
        const langButtons = document.querySelectorAll('.lang-btn');

        langButtons.forEach(btn => {
            const lang = btn.getAttribute('data-lang');
            if (lang === this.currentLanguage) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    }

    /**
     * Set up language switching event listeners
     */
    setupLanguageSwitching() {
        const langButtons = document.querySelectorAll('.lang-btn');

        langButtons.forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.preventDefault();
                const lang = btn.getAttribute('data-lang');
                await this.switchLanguage(lang);
            });
        });
    }

    /**
     * Format date according to current locale
     * @param {Date} date - Date to format
     * @param {object} options - Intl.DateTimeFormat options
     * @returns {string} Formatted date
     */
    formatDate(date, options = {}) {
        const locale = this.getLocale();
        const defaultOptions = {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        };

        return new Intl.DateTimeFormat(locale, { ...defaultOptions, ...options }).format(date);
    }

    /**
     * Format number according to current locale
     * @param {number} number - Number to format
     * @param {object} options - Intl.NumberFormat options
     * @returns {string} Formatted number
     */
    formatNumber(number, options = {}) {
        const locale = this.getLocale();
        return new Intl.NumberFormat(locale, options).format(number);
    }

    /**
     * Get current locale for Intl APIs
     * @returns {string} Locale code
     */
    getLocale() {
        const localeMap = {
            'fr': 'fr-FR',
            'ar': 'ar-SA',
            'en': 'en-US'
        };
        return localeMap[this.currentLanguage] || 'fr-FR';
    }

    /**
     * Load saved language preference
     */
    loadSavedLanguage() {
        const saved = localStorage.getItem('preferredLanguage');
        if (saved && ['fr', 'ar', 'en'].includes(saved)) {
            this.currentLanguage = saved;
        }
    }

    /**
     * Get current language
     * @returns {string} Current language code
     */
    getCurrentLanguage() {
        return this.currentLanguage;
    }

    /**
     * Check if current language is RTL
     * @returns {boolean} True if RTL
     */
    isRightToLeft() {
        return this.isRTL;
    }
}

// Global instance
window.i18n = new LocalizationSystem();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LocalizationSystem;
}

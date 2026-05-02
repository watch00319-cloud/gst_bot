"""
Multi-language message templates for GST Bot
"""

MESSAGES = {
    "en": {
        "welcome": (
            "👋 *Welcome to GST Nil Return Bot!*\n\n"
            "I am your professional assistant for *The Nutrition Hut*.\n\n"
            "🚀 *What I can do for you:*\n"
            "• ✅ *Easy GST Nil Filing*: File in seconds.\n"
            "• 🔔 *Monthly Reminders*: Never miss a deadline.\n"
            "• 🔒 *Secure Data*: Your data is fully encrypted.\n"
            "• ⚡ *Fast Process*: Automated portal login.\n\n"
            "Please select an option below:"
        ),
        "main_menu": "📍 *Main Menu*",
        "btn_status": "📊 GST Status",
        "btn_file": "📄 File Nil Return",
        "btn_settings": "⚙️ Settings",
        "btn_history": "📜 Filing History",
        "btn_support": "📞 Support",
        "unauthorized": "❌ *Unauthorized Access*\n\nThis bot is for authorized users only. Please contact the administrator.",
        "settings_title": "⚙️ *Bot Settings*\n\nConfigure your preferences below:",
        "btn_lang": "🌐 Change Language",
        "btn_reminders": "🔔 Reminders",
        "btn_back": "🔙 Back",
        "support_info": "📞 *Support Information*\n\nFor any issues, contact the administrator.\nBusiness: {business_name}\nGSTIN: {gstin}",
        "status_title": "📊 *Current GST Status*",
        "history_title": "📜 *Filing History*",
        "no_history": "No filing history found.",
        "admin_panel": "🔑 *Admin Control Panel*",
    },
    "hi": {
        "welcome": (
            "👋 *GST Nil Return Bot में आपका स्वागत है!*\n\n"
            "मैं *The Nutrition Hut* के लिए आपका प्रोफेशनल असिस्टेंट हूँ।\n\n"
            "🚀 *मैं आपकी कैसे मदद कर सकता हूँ:*\n"
            "• ✅ *आसान GST Nil Filing*: बस कुछ ही सेकंड में।\n"
            "• 🔔 *मासिक रिमाइंडर्स*: डेडलाइन कभी न भूलें।\n"
            "• 🔒 *सुरक्षित डेटा*: आपका डेटा पूरी तरह से एन्क्रिप्टेड है।\n"
            "• ⚡ *तेज़ प्रक्रिया*: ऑटोमेटेड पोर्टल लॉगिन।\n\n"
            "कृपया नीचे दिए गए विकल्पों में से चुनें:"
        ),
        "main_menu": "📍 *मुख्य मेनू*",
        "btn_status": "📊 GST स्टेटस",
        "btn_file": "📄 Nil रिटर्न भरें",
        "btn_settings": "⚙️ सेटिंग्स",
        "btn_history": "📜 पुराना रिकॉर्ड",
        "btn_support": "📞 सहायता",
        "unauthorized": "❌ *अनधिकृत पहुंच*\n\nयह बॉट केवल अधिकृत उपयोगकर्ताओं के लिए है। कृपया एडमिन से संपर्क करें।",
        "settings_title": "⚙️ *बॉट सेटिंग्स*\n\nअपनी पसंद के अनुसार कॉन्फ़िगर करें:",
        "btn_lang": "🌐 भाषा बदलें",
        "btn_reminders": "🔔 रिमाइंडर्स",
        "btn_back": "🔙 वापस",
        "support_info": "📞 *सहायता जानकारी*\n\nकिसी भी समस्या के लिए एडमिन से संपर्क करें।\nबिज़नेस: {business_name}\nGSTIN: {gstin}",
        "status_title": "📊 *वर्तमान GST स्टेटस*",
        "history_title": "📜 *फाइलिंग इतिहास*",
        "no_history": "कोई फाइलिंग इतिहास नहीं मिला।",
        "admin_panel": "🔑 *एडमिन कंट्रोल पैनल*",
    }
}

def get_text(key: str, lang: str = "en", **kwargs) -> str:
    """Get localized text"""
    text = MESSAGES.get(lang, MESSAGES["en"]).get(key, MESSAGES["en"].get(key, key))
    if kwargs:
        return text.format(**kwargs)
    return text

# Multi-Language Support Setup Guide

## Overview

This Django application now supports multiple languages including Ghanaian languages. The system is configured to support:

- **English** (en) - Default language
- **Akan** (ak) - Major Ghanaian language
- **Ewe** (ee) - Regional language
- **Ga** (ga) - Regional language  
- **Hausa** (ha) - Regional language
- **Twi** (tw) - Major Ghanaian language

## ✅ What's Already Implemented

### 1. Django Configuration
- ✅ **LocaleMiddleware** added to enable language switching
- ✅ **i18n context processor** added for template access
- ✅ **URL patterns** configured with `i18n_patterns`
- ✅ **Language settings** configured in `settings.py`
- ✅ **Timezone** set to Ghana (`Africa/Accra`)

### 2. Language Switcher Component
- ✅ **Dropdown component** created (`templates/language_switcher.html`)
- ✅ **Integrated** into both backoffice and application form headers
- ✅ **Flag icons** and proper styling
- ✅ **Form submission** to Django's `set_language` view

### 3. Template Integration
- ✅ **i18n tags** loaded in templates
- ✅ **Language attributes** set on HTML elements
- ✅ **Translation tags** added to key strings
- ✅ **Dynamic language** switching support

## 🚧 Next Steps Required

### 1. Install GNU Gettext Tools

To properly generate and compile translation files, you need to install GNU gettext:

#### Windows:
```bash
# Option 1: Manual Download (Recommended)
# Download from: https://mlocati.github.io/articles/gettext-iconv-windows.html
# Extract to C:\Program Files\gettext
# Add C:\Program Files\gettext\bin to your PATH environment variable

# Option 2: Using Chocolatey (if available)
choco install gettext

# Option 3: Using Scoop
scoop install gettext
```

#### Linux (Ubuntu/Debian):
```bash
sudo apt-get install gettext
```

#### macOS:
```bash
brew install gettext
```

### 2. Generate Translation Files

Once gettext is installed, run:

```bash
# Generate .po files for all languages
python manage.py makemessages --all

# Compile .mo files
python manage.py compilemessages
```

### 3. Add More Translations

Edit the generated `.po` files in `locale/[lang]/LC_MESSAGES/django.po` to add translations:

```po
# Example for Akan (ak)
msgid "Welcome to GCX Portal"
msgstr "Akwaaba wɔ GCX Portal mu"
```

### 4. Enable All Languages

Uncomment the language settings in `mysite/settings.py`:

```python
LANGUAGES = [
    ('en', _('English')),
    ('ak', _('Akan')),
    ('ee', _('Ewe')),
    ('ga', _('Ga')),
    ('ha', _('Hausa')),
    ('tw', _('Twi')),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]
```

## 📁 File Structure

```
project/
├── locale/                    # Translation files (after setup)
│   ├── en/LC_MESSAGES/
│   ├── ak/LC_MESSAGES/
│   ├── ee/LC_MESSAGES/
│   ├── ga/LC_MESSAGES/
│   ├── ha/LC_MESSAGES/
│   └── tw/LC_MESSAGES/
├── templates/
│   ├── language_switcher.html # Language switcher component
│   ├── application_form.html  # With i18n support
│   └── backoffice/
│       └── base.html          # With i18n support
└── mysite/
    ├── settings.py            # i18n configuration
    └── urls.py                # i18n URL patterns
```

## 🔧 Configuration Details

### Settings.py Changes

```python
# Middleware
MIDDLEWARE = [
    # ... other middleware
    'django.middleware.locale.LocaleMiddleware',  # Added
    # ... other middleware
]

# Templates
TEMPLATES = [
    {
        'OPTIONS': {
            'context_processors': [
                # ... other processors
                'django.template.context_processors.i18n',  # Added
            ],
        },
    },
]

# Internationalization
LANGUAGE_CODE = 'en'
LANGUAGES = [
    ('en', _('English')),
    ('ak', _('Akan')),
    ('ee', _('Ewe')),
    ('ga', _('Ga')),
    ('ha', _('Hausa')),
    ('tw', _('Twi')),
]
LOCALE_PATHS = [BASE_DIR / 'locale']
TIME_ZONE = 'Africa/Accra'
USE_I18N = True
USE_L10N = True
```

### URL Configuration

```python
# mysite/urls.py
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    # Non-internationalized URLs
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),  # Language switching
] + i18n_patterns(
    # Internationalized URLs
    path('', include('applications.urls')),
    path('accounts/', include('accounts.urls')),
    # ... other patterns
    prefix_default_language=False,
)
```

## 🌍 Language Switcher Usage

### In Templates

```html
{% load i18n %}
{% include 'language_switcher.html' %}
```

### Language Switching Flow

1. User clicks language in dropdown
2. Form submits to `/i18n/setlang/`
3. Django sets language in session
4. User is redirected back with new language
5. All subsequent requests use selected language

## 📝 Adding New Translations

### 1. Mark Strings in Templates

```html
{% load i18n %}
<h1>{% trans "Welcome to GCX Portal" %}</h1>
<p>{% trans "Please fill out the application form" %}</p>
```

### 2. Mark Strings in Python Code

```python
from django.utils.translation import gettext as _

def my_view(request):
    message = _("Welcome to our portal")
    return render(request, 'template.html', {'message': message})
```

### 3. Generate Translation Files

```bash
python manage.py makemessages --all
```

### 4. Edit Translation Files

Open `locale/[lang]/LC_MESSAGES/django.po` and add translations:

```po
msgid "Welcome to GCX Portal"
msgstr "Akwaaba wɔ GCX Portal mu"  # Akan translation
```

### 5. Compile Messages

```bash
python manage.py compilemessages
```

## 🎨 Language Switcher Styling

The language switcher includes:

- **Bootstrap dropdown** styling
- **Flag icons** for visual identification
- **Active state** highlighting
- **Responsive design**
- **Smooth transitions**

### Customization

Edit `templates/language_switcher.html` to customize:

- Flag icons
- Dropdown styling
- Language display names
- Button appearance

## 🔍 Testing Language Switching

1. **Start the server**: `python manage.py runserver`
2. **Visit the application**: Go to `/apply/` or backoffice
3. **Click language switcher**: Use dropdown in header
4. **Verify switching**: Check URL changes and content language
5. **Test persistence**: Refresh page to ensure language persists

## 🚨 Troubleshooting

### Common Issues

1. **"Can't find xgettext"**
   - Install GNU gettext tools
   - Ensure gettext is in PATH

2. **Translations not showing**
   - Check `.po` files have translations
   - Run `compilemessages`
   - Clear browser cache

3. **Language not persisting**
   - Ensure `LocaleMiddleware` is enabled
   - Check session configuration

4. **URL patterns not working**
   - Verify `i18n_patterns` usage
   - Check URL configuration

### Debug Commands

```bash
# Check Django configuration
python manage.py check

# List available languages
python manage.py diffsettings | grep -i language

# Test translation loading
python manage.py shell
>>> from django.utils.translation import activate
>>> activate('ak')
>>> from django.utils.translation import gettext
>>> gettext('Hello')
```

## 📚 Additional Resources

- [Django Internationalization Documentation](https://docs.djangoproject.com/en/stable/topics/i18n/)
- [GNU Gettext Manual](https://www.gnu.org/software/gettext/manual/)
- [Ghanaian Language Resources](https://en.wikipedia.org/wiki/Languages_of_Ghana)

## 🎯 Future Enhancements

1. **Automatic language detection** based on browser settings
2. **RTL support** for Arabic languages
3. **Pluralization rules** for complex translations
4. **Translation management** interface
5. **Language-specific date/number formatting**

---

**Status**: ✅ Basic multi-language infrastructure implemented
**Next**: Install gettext tools and add full translations

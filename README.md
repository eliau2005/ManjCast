# ManjCast

אפליקציה לשידור מסך למכשירי Chromecast במערכת Manjaro Linux.

## דרישות מערכת

- Python 3.9 או גרסה חדשה יותר
- Qt6
- FFmpeg
- wmctrl
- pipewire (עבור Wayland)

## התקנת דרישות המערכת

```bash
sudo pacman -S python qt6 ffmpeg wmctrl pipewire
```

## התקנת האפליקציה

### התקנה מהמקור

1. הורד את קוד המקור:
```bash
git clone https://github.com/eliau2005/ManjCast.git
cd manjcast
```

2. צור סביבת Python וירטואלית (אופציונלי אך מומלץ):
```bash
python -m venv venv
source venv/bin/activate
```

3. התקן את האפליקציה:
```bash
pip install .
```

### התקנת קיצור הדרך בתפריט היישומים

להתקנה עבור המשתמש הנוכחי בלבד:
```bash
mkdir -p ~/.local/share/applications
cp manjcast.desktop ~/.local/share/applications/
```

להתקנה מערכתית (עבור כל המשתמשים):
```bash
sudo cp manjcast.desktop /usr/share/applications/
```

## הרצת האפליקציה

לאחר ההתקנה, ניתן להריץ את האפליקציה בכמה דרכים:

1. דרך תפריט היישומים - חפש "ManjCast"
2. מהטרמינל - הקלד `manjcast`

## אייקון האפליקציה

האפליקציה משתמשת באייקון `cast-screen` מערכת הסמלים הסטנדרטית. אם ברצונך להשתמש באייקון מותאם אישית:

1. צור או הורד אייקון בגודל 256x256 פיקסלים בפורמט PNG
2. שמור את האייקון:
   - עבור משתמש יחיד: `~/.local/share/icons/hicolor/256x256/apps/manjcast.png`
   - עבור כל המשתמשים: `/usr/share/icons/hicolor/256x256/apps/manjcast.png`
3. עדכן את קובץ ה-desktop entry כך שיצביע על האייקון החדש:
   ```
   Icon=manjcast
   ```

## פיתוח

להתקנה במצב פיתוח:
```bash
pip install -e .
```

## רישיון

GPL v3

> BackEnd
```bash
python -m venv venv
source venv/Scripts/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```
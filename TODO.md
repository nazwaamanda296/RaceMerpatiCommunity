# Fixes to Implement

1. Fix import error in models/_init_.py
   - Change `from models.database import get_conn, hash_password` to `from models.database import get_conn` and add `from libs_utils import hash_password`

2. Fix deprecated rerun method in screens/inventory.py
   - Replace all instances of `st.experimental_rerun()` with `st.rerun()`

3. Create proper implementation for models/closing.py
   - Implement basic functionality for closing journal entries

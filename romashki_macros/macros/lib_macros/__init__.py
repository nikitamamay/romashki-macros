"""
Пакет `lib_macros` представляет собой модули с основополагающим функционалом
для работы с Компас-API и для создания макросов.

Ключевым является модуль `lib_macros.core`.

Пример применения:
1. Cтруктура файлов:
```
macros/
├─ lib_macros/
│ ├─ core.py
│ └─ ...
├─ custom_macros.py
└─ ...
```

2. Файл `custom_macros.py`:
```python
# рекомендуется:
from .lib_macros import core
from .lib_macros import selection_filter as lib_selection_filter
# допускается, но не рекомендуется:
from .lib_macros.core import *
```
"""

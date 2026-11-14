from pathlib import Path
import sys
from streamlit.testing.v1 import AppTest

pasta = Path(__file__).resolve().parent
sys.path.insert(0, str(pasta))
for pagina in [pasta / 'Inicio.py', *sorted((pasta / 'pages').glob('*.py'))]:
    for janela in ('2026', '2025'):
        app = AppTest.from_file(str(pagina), default_timeout=60)
        app.run()
        if janela == '2025':
            app.selectbox[0].select(janela).run()
        if app.exception:
            print(pagina.name, janela, 'ERRO', [e.message for e in app.exception])
            raise SystemExit(1)
        print(pagina.name, janela, 'OK')

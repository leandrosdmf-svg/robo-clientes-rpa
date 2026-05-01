# 🤖 Robô de Extração de Dados — RPA em Python

Automação web robusta para extrair dados de portais corporativos usando **Playwright + Python**.

## ✨ O Que Faz

- ✅ **Login automatizado** com detecção de pop-ups
- ✅ **Navegação resiliente** em portais web com retry automático
- ✅ **Extração de dados** de tabelas paginadas
- ✅ **Processamento de cards** e formulários
- ✅ **Salvamento duplo:** Excel local + Google Sheets
- ✅ **Sistema de licença** por hardware fingerprint (HMAC-SHA256)
- ✅ **Interface gráfica** com Tkinter
- ✅ **Distribuição .exe** com PyInstaller

## 📊 Case de Sucesso

**Robô para Corretora de Seguros**
- 📈 **85% de redução** no tempo de processamento
- ⚡ 8 horas/dia de trabalho → 30 min automático
- 🎯 Processa 100+ clientes por dia
- 🔄 Escalável — continua 24/7 sem parar

## 🛠️ Stack Tecnológico

| Tecnologia | Versão | Uso |
|------------|--------|-----|
| **Python** | 3.10+ | Orquestração principal |
| **Playwright** | 1.40+ | Browser automation |
| **Tkinter** | Built-in | Interface gráfica |
| **openpyxl** | 3.1+ | Manipulação Excel |
| **gspread** | 5.11+ | Integração Google Sheets |
| **cryptography** | 41.0+ | Criptografia Fernet |
| **PyInstaller** | 6.0+ | Geração do .exe |

## 📦 Instalação

### 1. Clone o repositório
```bash
git clone https://github.com/leandrosdmf-svg/robo-clientes-rpa.git
cd robo-clientes-rpa
```

### 2. Crie um ambiente virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Configure credenciais
```bash
cp config/.env.example .env
# Edite o arquivo .env com suas credenciais
```

## 🚀 Como Usar

### Interface Gráfica (Recomendado)
```bash
python main.py
```

### Terminal
```python
from src.robo import iniciar_robo

# Executar para CPF específico
iniciar_robo(
    headless=False,
    limite=100
)
```

## 📁 Arquitetura

robo-clientes-rpa/
├── main.py                    ← Interface Tkinter
├── config/
│   ├── settings.py            ← Configurações (lê .env)
│   └── .env.example           ← Template de credenciais
├── src/
│   ├── robo.py               ← Orquestrador principal
│   ├── login_porto.py        ← Fluxo de login
│   ├── extrator.py           ← Navegação e extração
│   └── licenca.py            ← Sistema de licença
├── requirements.txt
├── .gitignore
└── README.md

## 🔐 Segurança

- ✅ Credenciais em `.env` (não versionadas)
- ✅ Licença vinculada ao hardware (impossível reutilizar)
- ✅ Criptografia HMAC-SHA256 para validação
- ✅ Anti-bot Imperva: delays aleatórios + movimentos de mouse
- ✅ `.gitignore` rigoroso para dados sensíveis

## 📋 Funcionalidades Principais

### Login
- Detecção automática de pop-up de sessão ativa
- Preenchimento automático de código SUSEP
- Fechamento automático de pop-ups de propaganda

### Navegação
- Menu navigation com cliques sequenciais
- Auto-reload em caso de erro de Iframe
- Re-login automático em até 3 tentativas

### Extração
- Paginação automática
- Limite configurável de registros
- Regex para validação de CPF/CNPJ

### Saída
- Excel local: `dados/base_de_extracao.xlsx`
- Google Sheets: API gspread integrada
- Deduplicação automática

## 🤝 Contribuindo

Pull requests são bem-vindas! Para mudanças grandes:
1. Faça um fork
2. Crie uma branch (`git checkout -b feature/AmazingFeature`)
3. Commit seus changes (`git commit -m 'Add AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

MIT License — use livremente em projetos pessoais e comerciais

## 👨‍💻 Autor

**Leandro Cardoso** — RPA Specialist

- 🔗 LinkedIn: https://linkedin.com/in/leandrosdmf
- 📧 Email: leandrosdmf@gmail.com
- 🌐 GitHub: [github.com/leandrosdmf-svg](https://github.com/leandrosdmf-svg)

## 📞 Suporte

Para dúvidas, abra uma [issue](https://github.com/leandrosdmf-svg/robo-clientes-rpa/issues) neste repositório!

---

⭐ Se este projeto te ajudou, deixa uma star!

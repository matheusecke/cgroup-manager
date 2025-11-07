# CGroup Manager

Aplicação de gerenciamento de execução de scripts em ambientes isolados usando namespaces e cgroups.

## Estrutura do Projeto

```
cgroup-manager/
├── Vagrantfile               # VM provisionada via Vagrant
└── app/
    ├── main.py              # API FastAPI
    ├── database.py          # SQLite
    ├── environments.py      # Gerenciador de cgroups/namespaces
    ├── requirements.txt     # Dependências Python
    └── static/
        ├── index.html       # Interface web
        ├── style.css        # Estilos
        └── app.js           # JavaScript
```

## Como Usar

### 1. Iniciar a VM

```bash
vagrant up
```


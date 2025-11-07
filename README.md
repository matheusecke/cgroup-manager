# CGroup Manager

Aplicação simplificada para gerenciar execução de scripts em ambientes isolados usando namespaces e cgroups.

## Estrutura do Projeto

```
cgroups-environment/
├── Vagrantfile               # VM única com provisioning inline
└── app/
    ├── main.py              # API FastAPI
    ├── database.py          # SQLite puro (sem ORM)
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
cd cgroups-environment
vagrant up
```

O Vagrant irá:

- Criar VM Ubuntu 22.04 com 2 cores e 4GB RAM
- Instalar Python e dependências
- Criar diretórios necessários
- Iniciar aplicação automaticamente na porta 8000

### 2. Acessar a Interface

Abra no navegador:

- `http://localhost:8000` ou
- `http://192.168.56.20:8000`

### 3. Criar Ambientes

Na interface web:

1. Preencha o nome do ambiente
2. Configure recursos (CPU, Memória, I/O)
3. Escreva o script bash
4. Clique em "Criar Ambiente"

### 4. Gerenciar Ambientes

- **Ver Logs**: Clique em "Logs" para ver a saída do script
- **Parar**: Para ambientes em execução
- **Remover**: Remove completamente o ambiente

## Organização na VM

Os ambientes são organizados de forma simples e fácil de entender:

```
/sys/fs/cgroup/env_1/              → Cgroup do ambiente 1
/var/lib/cgroup-manager/env_1.sh   → Script bash
/var/lib/cgroup-manager/env_1.pid  → PID do processo
/var/log/cgroup-manager/env_1.log  → Logs de saída
/var/lib/cgroup-manager/database.db → Banco SQLite
```

### Inspecionar na VM

```bash
# Conectar na VM
vagrant ssh

# Ver cgroups criados
ls -la /sys/fs/cgroup/

# Ver detalhes do cgroup env_1
cat /sys/fs/cgroup/env_1/cpu.max
cat /sys/fs/cgroup/env_1/memory.max
cat /sys/fs/cgroup/env_1/cgroup.procs

# Ver scripts
ls -la /var/lib/cgroup-manager/

# Ver logs
tail -f /var/log/cgroup-manager/env_1.log

# Ver banco de dados
sqlite3 /var/lib/cgroup-manager/database.db "SELECT * FROM environments;"
```

## Funcionalidades

### Isolamento com Namespaces

Cada ambiente executa em namespaces isolados:

- **PID namespace**: Processos isolados
- **Mount namespace**: Sistema de arquivos isolado
- **UTS namespace**: Hostname isolado

### Controle de Recursos com Cgroups

Cada ambiente tem limites configuráveis:

- **CPU**: 0.1 a 2.0 cores
- **Memória**: 64 a 4096 MB
- **I/O Weight**: 100 a 1000

### Gerenciamento

- Criar ambientes com scripts bash
- Ver logs em tempo real
- Parar execução
- Remover completamente

## Comandos Úteis

```bash
# Reiniciar aplicação
vagrant ssh
sudo systemctl restart cgroup-manager

# Ver logs do serviço
sudo journalctl -u cgroup-manager -f

# Ver status
sudo systemctl status cgroup-manager

# Parar VM
vagrant halt

# Destruir VM
vagrant destroy
```

## Tecnologias

- **Backend**: Python 3, FastAPI, sqlite3
- **Frontend**: HTML, CSS, JavaScript vanilla
- **Infraestrutura**: Vagrant, VMware, Ubuntu 22.04
- **Isolamento**: Linux namespaces, cgroups v2

## Requisitos

- Vagrant
- VMware Desktop
- 4GB RAM disponível
- 2 cores CPU

## Arquitetura Simplificada

A aplicação foi projetada para ser **fácil de entender e explicar**:

1. **IDs Simples**: `env_1`, `env_2`, etc. (ao invés de UUIDs)
2. **SQLite Puro**: Sem ORM, apenas SQL direto
3. **Estrutura Clara**: Fácil navegar pelos diretórios
4. **Código Organizado**: Separado em módulos lógicos
5. **Provisioning Inline**: Tudo no Vagrantfile

## API Endpoints

- `GET /` - Interface web
- `POST /api/environments` - Criar ambiente
- `GET /api/environments` - Listar ambientes
- `GET /api/environments/{id}` - Detalhes do ambiente
- `GET /api/environments/{id}/logs` - Ver logs
- `POST /api/environments/{id}/stop` - Parar ambiente
- `DELETE /api/environments/{id}` - Remover ambiente
- `GET /health` - Health check



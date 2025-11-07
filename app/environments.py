import os
import subprocess
import signal
import time
from pathlib import Path


class EnvironmentManager:
    def __init__(self):
        self.cgroup_root = Path("/sys/fs/cgroup")
        self.base_dir = Path("/var/lib/cgroup-manager")
        self.logs_dir = Path("/var/log/cgroup-manager")
        
        # Criar diretórios necessários
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Habilitar controladores de cgroup uma vez no init
        self._enable_cgroup_controllers()
    
    def _enable_cgroup_controllers(self):
        """Habilita controladores de CPU, memória e I/O no cgroup raiz"""
        subtree_control = self.cgroup_root / "cgroup.subtree_control"
        
        if not subtree_control.exists():
            return
        
        for controller in ["cpu", "memory", "io"]:
            try:
                subtree_control.write_text(f"+{controller}\n")
            except OSError:
                # Controlador já habilitado ou não disponível
                pass
    
    def create_environment(self, env_id, name, cpu_limit, memory_mb, io_weight, script_content):
        """Cria e executa um novo ambiente isolado"""
        # Criar cgroup
        cgroup_path = self.cgroup_root / str(env_id)
        cgroup_path.mkdir(exist_ok=True)
        
        # Configurar limites de recursos
        self._set_cpu_limit(cgroup_path, cpu_limit)
        self._set_memory_limit(cgroup_path, memory_mb)
        self._set_io_weight(cgroup_path, io_weight)
        
        # Salvar script
        script_path = self.base_dir / f"{env_id}.sh"
        script_path.write_text(script_content)
        script_path.chmod(0o755)
        
        # Executar processo em namespace isolado
        log_file = self.logs_dir / f"{env_id}.log"
        
        command = [
            "unshare",
            "--pid",          # Namespace de processos
            "--mount",        # Namespace de montagens
            "--uts",          # Namespace de hostname
            "--fork",         # Fork
            "--mount-proc",   # Montar /proc no novo namespace
            "bash",
            str(script_path)
        ]
        
        with open(log_file, 'w') as log:
            process = subprocess.Popen(
                command,
                stdout=log,
                stderr=subprocess.STDOUT,
                preexec_fn=lambda: self._add_process_to_cgroup(cgroup_path)
            )
        
        # Salvar PID
        pid_file = self.base_dir / f"{env_id}.pid"
        pid_file.write_text(str(process.pid))
        
        return {
            "env_id": env_id,
            "pid": process.pid
        }
    
    def _set_cpu_limit(self, cgroup_path, cpu_limit):
        """Configura limite de CPU no cgroup"""
        # Converter cores para microsegundos
        # Ex: 0.5 cores = 50000 us a cada 100000 us (50%)
        cpu_quota = int(cpu_limit * 100000)
        cpu_period = 100000
        
        cpu_max_file = cgroup_path / "cpu.max"
        cpu_max_file.write_text(f"{cpu_quota} {cpu_period}\n")
    
    def _set_memory_limit(self, cgroup_path, memory_mb):
        """Configura limite de memória no cgroup"""
        memory_bytes = memory_mb * 1024 * 1024
        
        memory_max_file = cgroup_path / "memory.max"
        memory_max_file.write_text(f"{memory_bytes}\n")
    
    def _set_io_weight(self, cgroup_path, io_weight):
        """Configura peso de I/O no cgroup"""
        io_weight_file = cgroup_path / "io.weight"
        
        if io_weight_file.exists():
            try:
                io_weight_file.write_text(f"default {io_weight}\n")
            except OSError:
                # I/O pode não estar disponível em alguns sistemas
                pass
    
    def _add_process_to_cgroup(self, cgroup_path):
        """Adiciona o processo atual ao cgroup"""
        procs_file = cgroup_path / "cgroup.procs"
        procs_file.write_text(f"{os.getpid()}\n")
    
    def get_status(self, env_id):
        """Verifica se o processo está rodando"""
        pid = self._get_pid(env_id)
        
        if not pid:
            return "ERROR"
        
        try:
            # Signal 0 apenas verifica se o processo existe
            os.kill(pid, 0)
            return "RUNNING"
        except OSError:
            return "EXITED"
    
    def _get_pid(self, env_id):
        """Recupera o PID salvo do ambiente"""
        pid_file = self.base_dir / f"{env_id}.pid"
        
        if not pid_file.exists():
            return None
        
        try:
            return int(pid_file.read_text().strip())
        except (ValueError, OSError):
            return None
    
    def get_logs(self, env_id):
        """Retorna os logs do ambiente"""
        log_file = self.logs_dir / f"{env_id}.log"
        
        if not log_file.exists():
            return "Nenhum log disponível"
        
        return log_file.read_text()
    
    def stop_environment(self, env_id):
        """Para a execução do ambiente"""
        pid = self._get_pid(env_id)
        
        if not pid:
            return False
        
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)
            
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
            
            return True
        except OSError:
            return False
    
    def remove_environment(self, env_id):
        """Remove completamente o ambiente (processo + cgroup + arquivos)"""
        # Parar processo
        self.stop_environment(env_id)
        
        # Remover cgroup
        cgroup_path = self.cgroup_root / str(env_id)
        
        if cgroup_path.exists():
            # Matar todos os processos restantes no cgroup
            procs_file = cgroup_path / "cgroup.procs"
            
            if procs_file.exists():
                try:
                    pids = procs_file.read_text().strip().split('\n')
                    for pid_str in pids:
                        if pid_str:
                            try:
                                os.kill(int(pid_str), signal.SIGKILL)
                            except (OSError, ValueError):
                                pass
                except OSError:
                    pass
            
            time.sleep(0.5)
            
            # Remover diretório do cgroup
            try:
                cgroup_path.rmdir()
            except OSError:
                pass
        
        # Remover arquivos
        script_file = self.base_dir / f"{env_id}.sh"
        pid_file = self.base_dir / f"{env_id}.pid"
        log_file = self.logs_dir / f"{env_id}.log"
        
        for file_path in [script_file, pid_file, log_file]:
            try:
                file_path.unlink()
            except OSError:
                pass
        
        return True

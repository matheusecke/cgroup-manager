Vagrant.configure("2") do |config|
  config.vm.box = "bento/ubuntu-22.04"
  config.vm.hostname = "cgroup-manager"
  
  # Rede
  config.vm.network "private_network", ip: "192.168.56.20"
  config.vm.network "forwarded_port", guest: 8000, host: 8000, host_ip: "0.0.0.0"
  
  # Provider VMware
  config.vm.provider "vmware_desktop" do |v|
    v.vmx["memsize"] = "4096"
    v.vmx["numvcpus"] = "2"
  end
  
  # Sincronizar código da aplicação
  config.vm.synced_folder "./app", "/home/vagrant/app"
  
  # Provisioning inline completo
  config.vm.provision "shell", inline: <<-SHELL
    set -e
    
    echo "=== Atualizando sistema ==="
    apt-get update
    apt-get upgrade -y
    
    echo "=== Instalando Python e dependências ==="
    apt-get install -y python3 python3-pip python3-venv
    
    apt-get install -y stress
    
    echo "=== Criando diretórios necessários ==="
    mkdir -p /var/lib/cgroup-manager
    mkdir -p /var/log/cgroup-manager
    chmod 755 /var/lib/cgroup-manager
    chmod 755 /var/log/cgroup-manager
    
    echo "=== Verificando cgroups v2 ==="
    if [ ! -d "/sys/fs/cgroup/cgroup.controllers" ]; then
      echo "AVISO: cgroups v2 pode não estar habilitado"
    else
      echo "cgroups v2 detectado"
    fi
    
    echo "=== Instalando dependências Python ==="
    cd /home/vagrant/app
    pip3 install -r requirements.txt
    
    echo "=== Criando serviço systemd ==="
    cat > /etc/systemd/system/cgroup-manager.service <<'EOF'
[Unit]
Description=CGroup Manager API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/vagrant/app
ExecStart=/usr/local/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
    
    echo "=== Habilitando e iniciando serviço ==="
    systemctl daemon-reload
    systemctl enable cgroup-manager
    systemctl start cgroup-manager
    
    echo "Acesse a aplicação em: http://192.168.56.20:8000"
    echo "Ou via localhost: http://localhost:8000"
  SHELL
end




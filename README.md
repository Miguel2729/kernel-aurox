# Kernel Aurox

Kernel simuladl. Pode ser usado para criar distribuições personalizadas do sistema Aurox.

## 📁 Estrutura de Arquivos Esperada

Cada distribuição Aurox deve seguir esta estrutura:

Cada distribuição Aurox deve seguir esta estrutura:

#### sua_distribuicao/
#### ├──system/
#### │├── code/               # Códigos do sistema (obrigatório)
#### ││   ├── init.py         # Script de inicialização (opcional)
#### ││   └── *.py            # Outros serviços e daemons
#### │├── modules/            # Módulos Python personalizados
#### │├── tmp/                # Diretório para arquivos temporários
#### │└── shell               # Shell executável (obrigatório(script sh sem extensão))
#### ├──apps/                   # Aplicativos do sistema 
#### ├──mnt/                    # Ponto de montagem para filesystems
#### └──kernel.py               # Kernel principal (obrigatório)


### Descrição dos Diretórios

- **system/code/**: Contém todos os códigos do sistema que serão executados automaticamente
- **system/modules/**: Módulos Python adicionais para extensibilidade
- **system/tmp/**: Arquivos temporários do sistema
- **apps/**: Aplicativos instalados pelo usuário
- **mnt/**: Filesystems montados usando as funções `mnt()` e `configurar_fs()`

## 💡 Dicas para Desenvolvedores de Distribuições

### O que colocar em `system/code/`

- **init.py**: Script de inicialização principal (executado primeiro se existir)
- **Serviços do sistema**: Códigos que rodam em background
- **Daemons**: Processos de longa duração
- **Ferramentas**: Utilitários e comandos do sistema
- **Drivers**: Simulações de hardware usando `configurar_fs()`

### Exemplo de init.py
```python
# system/code/init.py
print("🚀 Inicializando Minha Distribuição Aurox...")

# Montar filesystems essenciais
mnt("rootfs", "sistema")

# Configurar conexões
configurar_fs("sistema", "diretorio", "/tmp", {"sync_mode": "mirror"})

# Iniciar serviços
print("✅ Sistema inicializado com sucesso")
```
Boas Práticas

1. Sempre testar serviços em ambiente controlado antes de distribuir
2. Evitar loops infinitos sem condições de saída
3. Usar matar_proc() para encerrar processos adequadamente
4. Documentar as funções personalizadas da sua distribuição
5. Verificar permissões do arquivo shell

## 🔧 Funções do Kernel Disponíveis

### Gerenciamento de Processes
```python
matar_proc(pid)
# Mata um processo pelo PID
# pid: ID do processo a ser terminado

listar_proc()
# Lista todos os processos ativos
# Retorna: None (sem processos) ou lista [[pid, nome], ...]
# Exemplo: [[0, "sys service 0"], [1, "sys service 1"]]

pwroff_krnl()
# desliga o sistema e depois o kernel
```
Gerenciamento de filesystems

mnt(fs, nomefs)
# Monta um filesystem
# fs: identificador do filesystem
# nomefs: nome do ponto de montagem
# Retorna: True (sucesso) ou False (falha)

umnt(nomefs)
# Desmonta um filesystem
# nomefs: nome do ponto de montagem
# Retorna: True (sucesso) ou False (falha)

configurar_fs(nomefs, tipo, destino, parametros={})
# Configura filesystem montado (também via comando cfgmnt)
# nomefs: filesystem montado
# tipo: 'hardware', 'diretorio', 'codigo_paralelo', 'rede'
# destino: path ou dispositivo
# parametros: configurações específicas do tipo

avisos importantes

· Não use em produção(embora possível): Este é um kernel educacional
· Teste extensivamente: Verifique todos os serviços em system/code/
· Cuidado com loops: Processos sem condições de saída podem travar o sistema
· Backup de dados: Sempre faça backup antes de testar novas distribuições
· Shell seguro: Verifique as permissões do arquivo shell da distribuição

🚀 Começando

1. Clone a estrutura base do Aurox
2. Adicione seus serviços em system/code/
3. Configure filesystems com mnt() e configurar_fs()
4. Teste a distribuição localmente
5. Distribua para outros usuários




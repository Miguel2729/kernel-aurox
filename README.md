# 🧠 Kernel Aurox

O **Kernel Aurox** é um kernel simulador projetado para criar **distribuições personalizadas** do sistema Aurox.  
Ele é **educacional** e permite montar e simular ambientes completos com suporte a processos, arquivos e sistemas de arquivos.

---

## 📁 Estrutura de Arquivos Esperada

Cada distribuição Aurox deve seguir esta estrutura:

```
sua_distribuicao/
├── system/
│   ├── code/              # Códigos do sistema (obrigatório)
│   │   ├── init.py        # Script de inicialização (opcional)
│   │   └── *.py           # Outros serviços e daemons
│   ├── modules/           # Módulos Python personalizados
│   ├── tmp/               # Diretório temporário do sistema
│   ├── apps/              # Aplicativos do sistema
│   └── shell              # Shell executável (opcional - script sh sem extensão)
├── mnt/                   # Ponto de montagem para filesystems
├── pkg/                   # pacotes instalados
└── kernel.py              # Kernel principal (obrigatório)
```

---

## 📦 Descrição dos Diretórios

- **system/code/** → Serviços e daemons do sistema  
- **system/modules/** → Módulos Python adicionais  
- **system/tmp/** → Arquivos temporários  
- **system/apps/** → Aplicativos do sistema  
- **mnt/** → Filesystems montados com `mnt()` e `configurar_fs()`
- **pkg/** → Pacotes instalados

---

## ⚙️ Classe `distro`

A classe `distro` é usada pelas distribuições Aurox para definir nome, versão, serviços, arquivos e IPC (comunicação entre processos).

### Exemplo:

```python
testsOS = distro(
	nome="MinhaDistro", ver="1.0",
	fs=["rootfs"], nomefs=["sistema"],
	cfgfs=[("diretorio", "/tmp", {"sync_mode": "mirror", "intervalo": 0.10})],
	services=["vfs.py", "audio.py", "tools.py"],
	serv_reset_m=False,
	ipc=True
	ufs=True # significa "umount filesystems on shutdown",
	pkgs=[["gabriel123", "editor"], ["enzo46321", "internet"]]
)
```

---

## 💡 Dicas para Desenvolvedores

### O que colocar em `system/code/`

- `init.py`: script de inicialização principal (o único a ser executado se existir)  
- Serviços e daemons em background    
- Drivers simulados(ou não) com `configurar_fs()`

### desenvolvimento pacotes aurox
---
deve ser hm repositório do github
estrutura do repositório:
```tree
[pacote]-aurox-pkg
└── [pacote].py
```
por exemplo se a distro tentar instalar um pacote chamado "editor", o aurox irá converter para "editor-aurox-pkg"
#### como dev ser [pacote].py?:
deve ser um módulo python, cada comando do pacote deve ser uma função(def), e a função main é obrigatória para comportamento padrão, todas as funções deve ter apenas um parâmetro, que vai ser uma tupla ou lista com todos os parâmetros da função

- não deve ter mais arquivos além do [pacote].py, se possível
---

### Exemplo de `init.py`

```python
print("🚀 Inicializando Minha Distribuição Aurox...")

# Montar filesystems essenciais
mnt("rootfs", "sistema")

# Configurar conexões
configurar_fs("sistema", "diretorio", "/tmp", {"sync_mode": "mirror", intervalo: 0.10})

print("✅ Sistema inicializado com sucesso!")
```

---

## 🔧 Funções do Kernel

### 🧠 Gerenciamento de Processos

```python
matar_proc(pid, log)
# Mata um processo pelo PID

listar_proc(printp)
# Lista todos os processos ativos
# Retorna: [[pid, nome], ...]

criar_processo_filho(pai, nome, codigo)
# cria um processo filho, o Parâmetro pai deve ser um pid numérico, de preferência de tipo int para o encerramento do pai encerrar o filho corretamente

CPFS(pai, nome, codigo)
# a mesma coisa criar_processo_filho, só que inicia no contexto do SYSC, apenas a distro(apps não) tem acesso ao CPFS
```

```python
pwroff_krnl()
# Desliga o sistema e encerra todos os processos

reboot()
# reinicia o sistema
```
### apps
```python
initapp(app, reset_m, log)
# log deve ser True ou False
# reset_m também
# se reset_m for True o initapp vai resetar a memória para iniciar o aplicativo
# diretorio recomendado de apps:
# system/apps
```

---

### 💾 Gerenciamento de Filesystems

```python
mnt(fs, nomefs)
# Monta um filesystem

umnt(nomefs)
# Desmonta um filesystem
configurar_fs(nomefs, tipo, destino, parametros)
# Configura um filesystem montado
# Tipos: 'hardware', 'diretorio', 'codigo_paralelo', 'rede'
# Parâmetros por tipo:
#   'hardware': sem parâmetros
#   'diretorio': sync_mode, criar_diretorio, intervalo
#   'codigo_paralelo': intervalo
#   'rede': protocolo, porta
#   'servidorweb': www_dir, protocolo, porta
#   'servidor': protocolo, porta, servidor_arquivos, servidor_servicos
# para obter mais informações pode olhar o código de kernel.py, não tem problema, é licença MIT
```

---

### 🔗 Comunicação entre Processos (IPC)

```python
IPC(destino, msg, assina_por_pid, assina_por_nome)
# Envia mensagem IPC para outro processo, assina_por_pid é o pid do remetente, assina_por_nome é o nome do remetente

ler_IPC(pid)
# Lê mensagens recebidas pelo processo

limpar_IPC(pid)
# Limpa o buffer IPC do processo
```
---
# 🗂 Gerenciamento de pacotes
```python
installpkg(dev, pkg)
# instala um pacote, github, requer git instalado

delpkg(pkg)
# deleta um pacote

usepkg(pkg, comando="main", parametros=())
# usa um pacote

checkpkg(pkg)
# verifica se um pacote existe
```

VED(pid, nome, x)
# Localiza processos ativos pelo PID ou nome.
# Retorna (True, valor_encontrado) ou (False, None).

# Parâmetros:
# pid (int): identificador do processo
# nome (str): nome do processo
# x (str): modo de busca
#           - "pid" → retorna o nome do processo a partir do PID
#           - "name" → retorna o PID a partir do nome

exemplo:
```
# Obter nome a partir do PID
ok, nome = VED(1, None, "pid")

# Obter PID a partir do nome
ok, pid = VED(None, "init", "name")
```
---
---
# namespaces do kernel
- o kernel executa namespaces separados para apps e a distro
namespaces:
```python
APPC = {
"__name__": __name__,
"VED": VED,
"matar_proc": matar_proc,
"listar_proc": listar_proc,
"IPC": IPC,
"ler_IPC": ler_IPC,
"limpar_IPC": limpar_IPC,
"criar_processo_filho": criar_processo_filho,
"__builtins__":  __builtins__,
"listpkg": listpkg,
"usepkg": usepkg,
"checkpkg": checkpkg
}

SYSC = {
'__name__': __name__,
"__builtins__": __builtins__,
"mnt": mnt,
"umnt": umnt,
"configurar_fs": configurar_fs,
"matar_proc": matar_proc,
"APPC": APPC,
"distro": distro,
"listar_proc": listar_proc,
"IPC": IPC,
"ler_IPC": ler_IPC,
"limpar_IPC": limpar_IPC,
"pwroff_krnl": pwroff_krnl,
"debug": debug,
"criar_processo_filho": criar_processo_filho,
"CPFS": CPFS,
"initapp": initapp,
'PHC': PHC,
"reboot": reboot,
"installpkg": installpkg,
"delpkg": delpkg,
"listpkg": listpkg,
"usepkg": usepkg,
"checkpkg": checkpkg
}

```
---

# ⚠️ Avisos Importantes

- ⚙️ pode ser usado em contextos educacionais, Simulações e produtivos
- 💾 cuidado com configurar_fs, ele não é simulado
- 🧪 Teste extensivamente os serviços antes de distribuir.  
- 🔁 while True em processos são modificados pelo kernel para parar em caso de encerrar o processo
- 🧹 Use `matar_proc()` e `pwroff_krnl()` para encerrar processos corretamente.  
- 🔐 Verifique permissões do arquivo `shell`.
- ✅️ os processos são executados dentro do kernel em contexto global, não como módulos separados, pode se comunicar(usar funções do kernel) com o kernel sem importar
- 📦 todos os processos tem um container criado pelo kernel, não é preciso se preocupar com o nome das variávei
---

## 🚀 Começando

1. Clone a estrutura base do Aurox  
2. Adicione seus serviços em `system/code/`  
3. Configure filesystems com `mnt()` e `configurar_fs()`  
4. Teste localmente  
5. Distribua sua versão do Aurox  

---

## 🧾 Exemplo de Desligamento

```
shutdown:
desligando...
encerrando processos...
⚠️ init encerrado
⚠️ vfs service encerrado
⚠️ audio service encerrado
⚠️ tools service encerrado
✅ ppn limpado
✅ limpado
Desmontando filesystems...
✅️ filesystems Desmontados
finalizando...
```

---

📘 **Versão:** Kernel Aurox  
📅 **Última atualização:** Outubro de 2025  
👨‍💻 **Autor:** Miguel  
🧩 **Licença:** MIT

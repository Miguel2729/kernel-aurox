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
│   └── shell              # Shell executável (obrigatório - script sh sem extensão)
├── mnt/                   # Ponto de montagem para filesystems
└── kernel.py              # Kernel principal (obrigatório)
```

---

## 📦 Descrição dos Diretórios

- **system/code/** → Serviços e daemons do sistema  
- **system/modules/** → Módulos Python adicionais  
- **system/tmp/** → Arquivos temporários  
- **system/apps/** → Aplicativos do sistema  
- **mnt/** → Filesystems montados com `mnt()` e `configurar_fs()`  

---

## ⚙️ Classe `distro`

A classe `distro` é usada pelas distribuições Aurox para definir nome, versão, serviços, arquivos e IPC (comunicação entre processos).

### Exemplo:

```python
testsOS = distro(
	"MinhaDistro", "1.0",
	["rootfs"], ["sistema"],
	[[("diretorio", "/tmp", {"sync_mode": "mirror"})]],
	["vfs.py", "audio.py", "tools.py"],
	serv_reset_m=None,
	ipc=True
)
```

---

## 💡 Dicas para Desenvolvedores

### O que colocar em `system/code/`

- `init.py`: script de inicialização principal (executado primeiro se existir)  
- Serviços e daemons em background  
- Ferramentas e utilitários de sistema  
- Drivers simulados com `configurar_fs()`  

### Exemplo de `init.py`

```python
print("🚀 Inicializando Minha Distribuição Aurox...")

# Montar filesystems essenciais
mnt("rootfs", "sistema")

# Configurar conexões
configurar_fs("sistema", "diretorio", "/tmp", {"sync_mode": "mirror"})

print("✅ Sistema inicializado com sucesso!")
```

---

## 🔧 Funções do Kernel

### 🧠 Gerenciamento de Processos

```python
matar_proc(pid, log=True)
# Mata um processo pelo PID

listar_proc(printp=True)
# Lista todos os processos ativos
# Retorna: [[pid, nome], ...]
```

```python
pwroff_krnl()
# Desliga o sistema e encerra todos os processos
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
```

---

### 🔗 Comunicação entre Processos (IPC)

```python
IPC(destino, msg, assinado_por)
# Envia mensagem IPC para outro processo

ler_IPC(pid)
# Lê mensagens recebidas pelo processo

limpar_IPC(pid)
# Limpa o buffer IPC do processo
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
ok, nome = VED(0, None, "pid")

# Obter PID a partir do nome
ok, pid = VED(None, "init", "name")
```

---

## ⚠️ Avisos Importantes

- ⚙️ Não use em produção — é um kernel educacional.  
- 🧪 Teste extensivamente os serviços antes de distribuir.  
- 🔁 Evite loops infinitos sem condição de saída.  
- 🧹 Use `matar_proc()` e `pwroff_krnl()` para encerrar processos corretamente.  
- 🔐 Verifique permissões do arquivo `shell`.
- ✅️ os processos são executados dentro do kernel em contexto global, não como módulos separados, pode se comunicar(usar funções do kernel) com o kernel sem importar

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
finalizando...
```

---

📘 **Versão:** Kernel Aurox  
📅 **Última atualização:** Outubro de 2025  
👨‍💻 **Autor:** Miguel  
🧩 **Licença:** MIT

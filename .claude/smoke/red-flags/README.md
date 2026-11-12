# smoke/red-flags — ver fallar el instrumento antes de fiarse de él

`agents/shared/red-flags.sh` es el grep compartido de Vera, Lidia e Ignacio. Ha fallado **tres
veces en silencio**, siempre hacia la buena noticia:

| Cuándo | Qué pasaba | Cómo se vio |
|---|---|---|
| iter-11 | el `TARGET` por defecto (`src`) no existe en este repo → todo «(clean)» | por casualidad |
| 2026-09-18 | **seis** checks (R5-R10) acababan en `\| head -N \|\| echo "(clean)"`, y `head` sale 0 siempre: no imprimían el hallazgo **ni** el «(clean)» | plantando violaciones |
| 2026-09-18 | **R1 no podía casar su propio caso**: la regex `-[a-z]+/85` no casa con `bg-blue-500/85` | plantando violaciones |

Los dos últimos solo aparecen si le pones delante un caso que DEBE cazar. Por eso existe esta
carpeta.

## Cómo se corre

```bash
bash .claude/agents/shared/red-flags.sh .claude/smoke/red-flags/sucio    # espera: 10 de 10
bash .claude/agents/shared/red-flags.sh .claude/smoke/red-flags/limpio   # espera:  0 de 10
bash .claude/agents/shared/red-flags.sh /ruta/que/no/existe              # espera: exit 2, NO «(clean)»
```

`sucio/` tiene **una** violación por comprobación (R1…R10) y `limpio/` es su gemelo conforme: las
mismas construcciones, bien escritas. Si tocas una regla, tienes que tocar los dos ficheros — una
regla que solo caza su caso plantado, o que también marca el gemelo limpio, no sirve.

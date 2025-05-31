# BugLens: LLM for taint-style bug analysis

## Quick Start

Please refer [BugLens](https://github.com/seclab-ucr/BugLens)


## Prompts

see `prompts/request.yaml` for the prompts used in the paper

this prompt is organized as follow:

```yaml
infer_variable_name:
    - text: # the text of the prompt (first prompt of a dialog)
      args: # the arguments to be passed to the LLM
        - arg1
        - arg2
    - text: # the text of the prompt (second prompt of a dialog)
smart_bug_analysis: # SecIA
    - text: # the text of the prompt (first prompt of the dialog)
      args: # the arguments to be passed to the LLM
        - arg1
        - arg2
      callback: # PKA, for source code retrieval
        - callback1
        - callback2
    - text: # the text of the prompt (second prompt of the dialog)
    ...
sanitizer_detection: # ConA
    ...
```


## Workflow

see `prompts/llm_analysis.py` for the details of the code implementation of the workflow.

### 1 - From static analysis results

for a static analysis result (e.g., suture) or codeql (a sarif file), parse the result and extract the relevant information 

`common/config.py` records the configuration of these analysis results, as follows:

```python
PROJ_CONFIG = { 
...
    "codeql/ioctl-to-cfu": {
        "proj_dir": ...
        "sarif_file": "results.sarif",
    },
...
}
```

see `parse_sarif.py` for the parsing of the sarif file


### 2 - Infer variable names

(not appearing in the paper)

the infer_variable_name prompt is used to infer the variable names from the static analysis which is based on LLVM passes. it converts the variable names in IR level to a source code level.

Therotically, this step is not necessary, as the debug information should be able to provide the variable names in the source code level. However, in practice (you know, so many corners), the debug information is not always available or accurate. So we directly let LLM handle this.

### 3 - Smart bug analysis (SecIA)

the smart_bug_analysis is the "SecIA" in the paper. It is used to analyze the static analysis results and to see if the current sink could be possible to be exploited. 

### 4 - Sanitizer detection (ConA)
the sanitizer_detection is the "ConA" in the paper. It is used to detect if the current sink (if exploitable) is protected by a sanitizer.

It's a very complex task, previous steps faces a fixed "context" from the static analysis (where the function of the sink). But sanitizer could be distant along the call graph. Threfore, we need to let LLM to retrieve the source code from its source to the sink (a complete call chain), and search any functions that could be a sanitizer (e.g., `validate_xxx()`).

After it found correct places of the sanitizers, it is then able to analyze the sanitizers' pre-/post-conditons, and summarize all of them to see if the sink is protected by the merge of sanitizers. 

### 5 - callbacks (PKA)

see `helper/callbacks.py` for the implementation of the callbacks.

the PKA is used to retrieve the source code from the source code repository. Currently, it supports the following callbacks:

```yaml
   - need_func_def
   - need_caller
   - need_struct_def
   - need_global_var_def
```


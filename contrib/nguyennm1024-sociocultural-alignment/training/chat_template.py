"""Llama-3.2 chat template with {% generation %} tags.

Two purposes:
  * deterministic, system-preamble-free framing (cultural default lives in the
    weights, not a system prompt — matches the dataset design), and
  * the {% generation %} block lets `return_assistant_tokens_mask` work, which
    is what TRL's `assistant_only_loss` uses to compute loss on the assistant
    turn (THINK+ANSWER+<|eot_id|>) only.
"""

CHAT_TEMPLATE = (
    "{{- bos_token }}"
    "{%- for message in messages %}"
    "{%- if message['role'] == 'assistant' %}"
    "{{- '<|start_header_id|>assistant<|end_header_id|>\n\n' }}"
    "{% generation %}{{- (message['content'] | trim) + '<|eot_id|>' }}{% endgeneration %}"
    "{%- else %}"
    "{{- '<|start_header_id|>' + message['role'] + '<|end_header_id|>\n\n' + (message['content'] | trim) + '<|eot_id|>' }}"
    "{%- endif %}"
    "{%- endfor %}"
    "{%- if add_generation_prompt %}"
    "{{- '<|start_header_id|>assistant<|end_header_id|>\n\n' }}"
    "{%- endif %}"
)

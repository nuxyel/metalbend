# read-bf16: two SmolLM2-135M decoder layers' weights (18 tensors, 7,080,192 numbers) read as BF16 from a safetensors
# file (data/bf16.safetensors, from lib/gen_bf16.py) with bendtorch-load's reader, the path a BendTorch model takes from
# a Hugging Face checkpoint: the header lexed and parsed in plain Bend, then each tensor, in the model's order (not the
# file's), read by bend-ml-binary-read's BF16 effect and widened exactly to F32 into one array. Prints the hash of the
# numbers.
import Base
import bendtorch-load@1.2.0.0/main.bend as L
import ../../lib/mb.bend as MB

def sq(+r: U32, +c: U32) -> List<&2, U32>:
  Con{r, Con{c, Nil{}}}

def vec(+n: U32) -> List<&2, U32>:
  Con{n, Nil{}}

# one decoder layer's tensors, in the model's order, prepended to rest
def layer(+p: String, rest: List<&2, L.Entry>) -> List<&2, L.Entry>:
  Con{L.Entry{p ++ "input_layernorm.weight", vec(576)},
  Con{L.Entry{p ++ "self_attn.q_proj.weight", sq(576, 576)},
  Con{L.Entry{p ++ "self_attn.k_proj.weight", sq(192, 576)},
  Con{L.Entry{p ++ "self_attn.v_proj.weight", sq(192, 576)},
  Con{L.Entry{p ++ "self_attn.o_proj.weight", sq(576, 576)},
  Con{L.Entry{p ++ "post_attention_layernorm.weight", vec(576)},
  Con{L.Entry{p ++ "mlp.gate_proj.weight", sq(1536, 576)},
  Con{L.Entry{p ++ "mlp.up_proj.weight", sq(1536, 576)},
  Con{L.Entry{p ++ "mlp.down_proj.weight", sq(576, 1536)}, rest}}}}}}}}}

def main() -> IO(Unit):
  do IO<Unit>:
    a : Array<F32> <- L.tensors("data/bf16.safetensors", 7080192, layer("model.layers.0.", layer("model.layers.1.", Nil{})))
    MB.show_hash(MB.hash(7080192n, a))

// read-bf16's target: data/bf16.safetensors's header read and searched for each tensor in the model's order (its
// dtype, shape and data_offsets checked), then each tensor's BF16 numbers read with one fread and widened exactly into
// the F32 array (the BF16 as the top 16 bits, the low 16 zero), then hashed. Bend's flags: clang -std=c11 -O3.
#include <inttypes.h>

#include "../../lib/mb.h"

enum { N = 7080192, HID = 576, KV = 192, FF = 1536 };

static const char *const PATH = "data/bf16.safetensors";

static void die(const char *what) { fprintf(stderr, "%s: %s\n", PATH, what); exit(1); }

// the entry of tensor `name` in the header: its BF16 dtype and its shape checked, its byte range returned
static void find(const char *hdr, const char *name, int rows, int cols, uint64_t *b, uint64_t *e) {
  char key[128], shape[64];
  snprintf(key, sizeof key, "\"%s\":{", name);
  const char *p = strstr(hdr, key);
  if (!p) die("a tensor is not in the file");
  const char *end = strchr(p, '}');
  const char *dt = strstr(p, "\"dtype\":\"BF16\"");
  if (!dt || dt > end) die("a tensor is not BF16");
  if (cols) snprintf(shape, sizeof shape, "\"shape\":[%d,%d]", rows, cols);
  else snprintf(shape, sizeof shape, "\"shape\":[%d]", rows);
  const char *sh = strstr(p, shape);
  if (!sh || sh > end) die("a tensor has another shape");
  const char *of = strstr(p, "\"data_offsets\":[");
  if (!of || of > end || sscanf(of, "\"data_offsets\":[%" SCNu64 ",%" SCNu64 "]", b, e) != 2) die("no data_offsets");
}

static const char *const PARTS[] = {"input_layernorm", "self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj",
                                    "self_attn.o_proj", "post_attention_layernorm", "mlp.gate_proj", "mlp.up_proj",
                                    "mlp.down_proj"};
static const int SHAPES[][2] = {{HID, 0}, {HID, HID}, {KV, HID}, {KV, HID}, {HID, HID}, {HID, 0}, {FF, HID},
                                {FF, HID}, {HID, FF}};

int main(void) {
  float *a = mb_zeros(N);
  uint16_t *buf = malloc(2 * (size_t)FF * HID);
  FILE *f = fopen(PATH, "rb");
  uint64_t len = 0;
  if (!f || !buf || fread(&len, 8, 1, f) != 1 || len > 100000000) die("no safetensors header");
  char *hdr = malloc(len + 1);
  if (!hdr || fread(hdr, 1, len, f) != len) die("the header is cut short");
  hdr[len] = 0;
  size_t at = 0;
  for (int l = 0; l < 2; l++)
    for (int t = 0; t < 9; t++) {
      char name[96];
      snprintf(name, sizeof name, "model.layers.%d.%s.weight", l, PARTS[t]);
      size_t n = (size_t)SHAPES[t][0] * (SHAPES[t][1] ? SHAPES[t][1] : 1);
      uint64_t b, e;
      find(hdr, name, SHAPES[t][0], SHAPES[t][1], &b, &e);
      if (e - b != 2 * n) die("data_offsets do not span a tensor");
      if (fseek(f, (long)(8 + len + b), SEEK_SET) || fread(buf, 2, n, f) != n) die("short read");
      for (size_t i = 0; i < n; i++) a[at + i] = u2f((uint32_t)buf[i] << 16);
      at += n;
    }
  fclose(f);
  mb_show_hash(a, N);
  return 0;
}

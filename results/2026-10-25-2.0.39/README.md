# 2026-10-25-2.0.39: release.sh's first run (plan v1, step 2)

`./release.sh 2.0.39`: both releases built from their tags with bun, the corpus at 1 and 16 threads, 5 rounds, 2m13s
in all. It finds on its own what plan v0 found: softmax-ce and mnist-step on 2.0.38 run 183% and 37% more
instructions than on 2.0.39, the same bytes; nothing else moved.

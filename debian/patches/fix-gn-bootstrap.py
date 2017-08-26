Index: dev/tools/gn/bootstrap/bootstrap.py
===================================================================
--- dev.orig/tools/gn/bootstrap/bootstrap.py
+++ dev/tools/gn/bootstrap/bootstrap.py
@@ -348,7 +348,7 @@ def write_gn_ninja(path, root_gen_dir, o
         '-pipe',
         '-fno-exceptions'
     ])
-    cflags_cc.extend(['-std=c++11', '-Wno-c++11-narrowing'])
+    cflags_cc.extend(['-std=gnu++14', '-Wno-c++11-narrowing'])
     if is_aix:
      cflags.extend(['-maix64'])
      ldflags.extend([ '-maix64 -Wl,-bbigtoc' ])

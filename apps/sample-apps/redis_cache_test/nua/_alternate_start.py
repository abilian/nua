from nua.lib.exec import exec_as_nua

cmd = "python -c 'from redis_cache_test.app import main; main()'"

exec_as_nua(cmd)

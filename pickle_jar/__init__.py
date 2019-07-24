import pickle
import os
import inspect


class pickle_jar(object):

    def __init__(self, output=None, invalidate=False, detect_changes=True,
                 cache_dir='pickle_jar/jar', verbose=False, check_args=False):
        self.invalidate = invalidate
        self.cache_dir = cache_dir
        self.detect_changes = detect_changes
        self.verbose = verbose
        self.check_args = check_args
        try:
            os.mkdir(cache_dir)
        except FileExistsError:
            pass
        self.output_res = output

    def __call__(self, func, *args, **kwargs):

        def new_func(*args, **kwargs):
            if not self.output_res:
                self.output_path = f'pickle_jar/jar/{func.__name__}'
                self.output_res = f'{self.output_path}/results.pickle'
            if not os.path.exists(self.output_path):
                os.makedirs(self.output_path)
            source = inspect.getsource(func)
            source = '\n'.join(source.split('\n')[1:])
            func_args = (hash(pickle.dumps(args)), hash(pickle.dumps(kwargs)))
            if os.path.exists(self.output_res) and not self.invalidate:
                with open(self.output_res, 'rb') as rb:
                    try:
                        res, cached_source, cached_func_args = pickle.load(rb)
                    except ValueError:
                        print("Issue parsing pickle cache, reloading")
                        res = func(*args, **kwargs)
                        return self.to_cache(res, source, func_args)
                    if self.detect_changes:
                        args_checked = True
                        if self.check_args:
                            try:
                                args_checked = func_args[0] == \
                                               cached_func_args[0] and \
                                               func_args[1] == \
                                               cached_func_args[1]
                            except TypeError:
                                print(
                                    "Issue checking function args: Only "
                                    "immutable function args can be checked "
                                    "with the `check_args` flag")
                                pass
                        if source == cached_source and args_checked:
                            if self.verbose:
                                print(f"Function \'{func.__name__}\'"
                                      f" source code unchanged")
                            return res
                        else:
                            if self.verbose:
                                print(f"Function \'{func.__name__}\' "
                                      f"source code changed, invalidating "
                                      f"cache")
                    else:
                        if self.verbose:
                            print(f"Updating cached source code for"
                                  f" function \'{func.__name__}\'")
                        return self.to_cache(res, source, func_args)

            res = func(*args, **kwargs)
            return self.to_cache(res, source, func_args)

        return new_func

    def to_cache(self, res, source, func_args):
        cache_entry = (res, source, func_args)
        with open(self.output_res, 'wb+') as wb:
            pickle.dump(cache_entry, wb)
        return res

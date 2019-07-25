import pickle
import os
import inspect
import hashlib
import json


class pickle_jar(object):

    def __init__(self, output=None, reload=False, detect_changes=True,
                 cache_dir='pickle_jar/jar', verbose=False, check_args=True):
        self.reload = reload
        self.cache_dir = cache_dir
        self.detect_changes = detect_changes
        self.verbose = verbose
        self.check_args = check_args
        try:
            os.mkdir(cache_dir)
        except FileExistsError:
            pass
        self.output_res = output

    def try_serialize(self, arg):
        argstr = ''
        try:
            argstr = arg.to_json().encode('utf-8')
        except AttributeError:
            try:
                argstr = json.dumps(arg).encode('utf-8')
            except TypeError:
                pass
        return argstr

    def try_hash(self, argstr):
        try:
            arghash = hashlib.md5(argstr).hexdigest()
        except TypeError:
            arghash = hashlib.md5(argstr.encode('utf-8')).hexdigest()
        return arghash

    def __call__(self, func, *args, **kwargs):

        def new_func(*args, **kwargs):
            # Hash function arguments
            output_args_str = ''
            if self.check_args:
                if self.output_res:
                    print(
                        "Cannot use `check_args` flag when specifying an "
                        "output path")
                else:
                    args_hashed = []
                    for arg in [*args, *[v for v in kwargs.values()]]:
                        argstr = self.try_serialize(arg)
                        arghash = self.try_hash(argstr)
                        args_hashed.append(arghash)

                    argstr_all = ''.join(sorted(args_hashed))
                    arghash_all = self.try_hash(argstr_all)

                    if self.check_args:
                        output_args_str = f'_{arghash_all}'

            # Create result output path
            if not self.output_res:
                self.output_path = f'pickle_jar/jar/{func.__name__}'
            if not os.path.exists(self.output_path):
                os.makedirs(self.output_path)

            self.output_res = f'{self.output_path}/' \
                f'results{output_args_str}.pickle'

            # Get function source code
            source = inspect.getsource(func)
            source = '\n'.join([line for line in source.split('\n') if
                                not line.strip().startswith('@')])

            # Decide whether to use cached or to reload
            if os.path.exists(self.output_res) and not self.reload:
                try:
                    res, cached_source = self.load_from_cache()
                except ValueError:
                    print("Issue parsing pickle cache, reloading")
                    return self.reload_cache(func, source, *args, **kwargs)
                if self.detect_changes:
                    # Load from cache if source codes match
                    if source == cached_source:
                        if self.verbose:
                            print(f"Function \'{func.__name__}\'"
                                  f" source code unchanged")
                        return res
                    # Reload cache if sources don't match
                    else:
                        if self.verbose:
                            print(f"Function \'{func.__name__}\' "
                                  f"source code changed, invalidating "
                                  f"cache")
                        return self.reload_cache(func, source, *args,
                                                 **kwargs)
                else:
                    # Update cache with newest function source code
                    if self.verbose:
                        print(f"Updating cached source code for"
                              f" function \'{func.__name__}\'")
                    return self.to_cache(res, source)
            return self.reload_cache(func, source, *args,
                                     **kwargs)

        return new_func

    def load_from_cache(self):
        with open(self.output_res, 'rb') as cache_file:
            self.output_res = None
            return pickle.load(cache_file)

    def reload_cache(self, func, source, *args, **kwargs):
        res = func(*args, **kwargs)
        return self.to_cache(res, source)

    def to_cache(self, res, source):
        cache_entry = (res, source)
        with open(self.output_res, 'wb+') as wb:
            pickle.dump(cache_entry, wb)
        self.output_res = None
        return res

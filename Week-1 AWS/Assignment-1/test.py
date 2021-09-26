from pathlib import Path, PurePath
p = PurePath('foo', 'some/path', 'bar',"..","..","..")
a = Path()
print(a)
print(p)
print(a==p)
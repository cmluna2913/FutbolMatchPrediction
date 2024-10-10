# FutbolMatchPrediction
I predict futbol matches. I'm starting out with MLS for now.

## Environment
If you want to recreate my environment, run this:

```
conda env create -f environment.yml
```
If you wanted to know how to export any environment (this excludes the "prefix"
which would normally include the path to your environment):
```
conda env export | grep -v "^prefix: " > environment.yml
```

---
STORE=ev-data.h5

for i in ev/ERCOT*.xls; 
do 
	bn=$(basename $i)
	name=${bn%.*}
	echo $name $i
	python3 lib/em-psse/scripts/ev.py  -n "${name}" --input "${i}" --store ${STORE}
done

for i in ev/ERCOT*.raw; 
do 
	bn=$(basename $i)
	name=${bn%.*}
	echo "Parse Raw ${name} $i"
	echo "python3 lib/em-psse/network.py --input \"$i\" --name \"${name}\" --export --store ev-data.h5"
	python3 lib/em-psse/network.py --input "$i" --name "$name" --export --store ${STORE} --refresh
done


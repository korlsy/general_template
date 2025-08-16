### [ simple-hooks-script-map ]
	
helm create hooks-v2

helm package hooks-v2/

helm repo index .

helm repo list

helm repo update my-helm-repo

helm search repo my-helm-repo

kubectl create ns demo

helm install simple-hooks-script-map my-helm-repo/simple-hooks-script-map -n demo 
	[helm install simple-hooks-script-map ./simple-hooks-script-map -n demo]
	
helm uninstall simple-hooks-script-map -n demo

---
### deploy
rm -f ./hooks-v2-*tgz;helm package hooks-v2/;helm repo index .;

git add .;git commit -m "c";git push

helm repo update my-helm-repo;helm search repo my-helm-repo



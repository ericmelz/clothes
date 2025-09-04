set -x

# Copy site to nginx-data repo
rsync -avz --delete output/ $HOME/Data/code/nginx-data/www/ericmelz.site

# Push site using github actions
CWD=$PWD
cd $HOME/Data/code/nginx-data
git status
git add *
git status
git commit -m"Updated clothes site"
git push
cd $PWD

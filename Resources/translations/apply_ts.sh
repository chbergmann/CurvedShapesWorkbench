#sudo apt install qttools5-dev-tools
for f in *_*.ts
do
    lrelease "$f"
done
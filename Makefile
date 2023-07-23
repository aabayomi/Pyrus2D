cleanall:
	rm -fr keeper_Q*.gz taker_Q*.gz logs/* *.lock core core.* vgcore.* 
	rm -fr *.lock console.log nohup.out *.dot *.xml
	rm -fr keeper_Q*.log
	rm -fr taker_Q*.log
	rm -fr python_debug.log
	rm -fr player*
	rm -fr *.rcg *.rcl
	./kill.sh 
	killall -q keepaway_player 1>/dev/null 2>&1

<template>
  <div id="app">
    <h3>用户帐号查询 v2.0</h3>
	<div>
		<textarea v-model="usernames" placeholder="用户帐号"></textarea>
	</div>
	<div>
		<button v-bind:disabled="isButtonDisabled" @click="findallusers">{{btntext}}</button>
	</div>
    <!-- <HelloWorld :userids="usernames"/> -->
	<HelloWorld :userids="userinfo"/>
	
  </div>
</template>

<script>
import HelloWorld from './components/HelloWorld.vue'
import axios from 'axios'

export default {
  name: 'App',
  components: {
    HelloWorld
  },
  data:function(){
	return{
		isButtonDisabled:false,
		btntext: '查 询',
		usernames:'',
		userinfo:[]
	}
  },
  methods:{
	getusers:function(){
		let username = this.usernames.split(/[\n, ]/)
		username = username.filter(s=>{return s && s.trim()})
		// console.log(username);
		
		
		// 准备通过axios发起查询请求
		// 存储所有http请求
		let reqList = []
		// 存储后台响应每个请求后的返回结果
		let resList = []
		
		// axios.default.baseURL='http://localhost:8080/api'
		for(let userid of username){
			// reqList.push(axios.get(`http://localhost:8080/api/username/${userid}`))
			reqList.push(axios.get(`http://192.168.108.102:8984/username/${userid}`))
			resList.push(`post${userid}`)
		}
		
		return axios.all(reqList)
		.then(axios.spread(function (...resList) {
			return resList // 拿到所有posts数据
		}))
	},
	findallusers:async function(){
		
		// 关闭查询按钮
		this.isButtonDisabled = true
		this.btntext = '正在查询，请稍后...'
		
	// async findallusers(){
		let responses = await this.getusers()
		// 清除结果数组,备用
		this.userinfo.splice(0)
		for (let i = 0; i < responses.length; i++) {
			if (responses[i] && responses[i].status === 200) {
				let datainfo = JSON.parse(responses[i].data)
				console.log(datainfo)
				this.userinfo.push(datainfo)
			}
		}
		
		// 开启查询按钮
		this.isButtonDisabled = false
		this.btntext = '查 询'
	}
	
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
textarea {
	width:  300px;
	height: 100px;
}
</style>

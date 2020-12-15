<template>
  <div class="hello">
    <h2>查询结果</h2>
	<table class="table_head" border="1px" align="center">
		<thead>
			<tr>
				<th width="30px" rowspan="2">SN</th>
				<th width="400px" colspan="4">用户</th>
				<th width="460px" colspan="4">OLT</th>
				<th width="368px" colspan="3">BRAS</th>
				<th width="200px" colspan="2">NAT</th>
				<th width="100px" rowspan="2">备注</th>
			</tr>
			<tr>
				<th width="120px">帐号</th>
				<th width="120px">IP</th>
				<th width="60px">Pool</th>
				<th width="100px">Qos</th>
				
				<th width="180px">名称</th>
				<th width="120px">IP</th>
				<th width="100px">Vlan</th>
				<th width="60px">ONU</th>
				
				<th width="128px">名称</th>
				<th width="120px">IP</th>
				<th width="120px">接口</th>
				
				<th width="100px">Hillstone</th>
				<th width="100px">Panabit</th>				
			</tr>
		</thead>
		<tbody>
			<template v-for="(value, index) in users">
				<template v-if="value.info.userip.length>1">
					<ListItem :index= index+1 :user=value trbackcolor="#55ff7f" :key=index></ListItem>
				</template>
				<template v-else>
					<ListItem :index= index+1 :user=value trbackcolor="#ffffff" :key=index></ListItem>
				</template>
			</template>
		</tbody>
	</table>
  </div>
</template>

<script>
import ListItem  from './ListItem.vue'

export default {
  name: 'UserList',
  components:{ListItem},
  props: {
	users: Array
  },
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.table_head {
	border-collapse: collapse;
	margin: 10px auto;
	height: 100%;
	width:  1500px;
	padding: 0;
	/*vertical-align: bottom;*/
	}

th {
	text-align:center;
	background-color:#337ab7;
	color:#FFFFFF;
}
	
h3 {
  margin: 40px 0 0;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
}
a {
  color: #42b983;
}
</style>


Vagrant.configure("2") do |config|

  config.vm.box = "trusty64"

  config.vm.box_url = "https://vagrantcloud.com/ubuntu/boxes/trusty64/versions/14.04/providers/virtualbox.box"

  config.vm.network :private_network, ip: "10.0.100.20"
  config.vm.network :forwarded_port, host: 5432, guest: 5432    # postgres
  config.vm.network :forwarded_port, host: 6379, guest: 6379    # redis
  config.vm.network :forwarded_port, host: 9200, guest: 9200    # elasticsearch
  config.vm.hostname = "develop.pinboard-archiver-2.com"

  config.vm.provision "ansible" do |ansible|
    ansible.groups = {
      "searchers" => ["default"],
      "workers" => ["default"],
      "db" => ["default"]
    }
    ansible.playbook = "provisioning/vagrant.yml"
    # ansible.verbose = "vvvv"
  end

end

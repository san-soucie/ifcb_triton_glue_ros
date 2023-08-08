import rospy
from sgdrf_msgs.msg import CategoricalObservation
from triton_image_classifier.msg import Classification
from sensor_msgs.msg import NavSatFix
from geometry_msgs.msg import Point

class Node:
    def __init__(self) -> None:
        rospy.init_node('ifcb_triton_glue')
        self.skip_pub_if_no_fix = rospy.get_param('~skip_pub_if_no_fix', True)
        self.classlist_file = rospy.get_param('~classlist_file')
        with open(self.classlist_file, 'r') as f:
            lines = f.read()
        self.classlist = lines.replace('\n', ',').split(',')
        class_topic = rospy.get_param('~topic') + '/class'
        sgdrf_obs_topic = f"categorical_observation__{rospy.get_param('~num_words')}__"
        self.sgdrf_obs_publisher = rospy.Publisher(sgdrf_obs_topic, CategoricalObservation, queue_size=10)
        self.class_subscriber = rospy.Subscriber(class_topic, Classification, self.callback)
        self._latest_fix = None
        self.gps__subscriber = rospy.Subscriber('/gps/fix', NavSatFix, self.latest_fix_setter)
    
    def spin(self):
        rospy.spin()

    
    @property
    def latest_fix(self):
        return self._latest_fix
    
    @latest_fix.setter
    def latest_fix(self, value):
        self._latest_fix = value

    def latest_fix_setter(self, value):
        self.latest_fix = value
    
    def callback(self, msg: Classification):
        best = self.classlist.index(max(msg.results, key = lambda x: x.score).class_)
        obs = [1 if i == best else 0 for i in range(rospy.get_param('~num_words'))]
        current_fix = self.latest_fix
        point = None
        if current_fix == None:
            if self.skip_pub_if_no_fix:
                rospy.logwarn('No GPS fix available. Skipping publishing.')
                return
            else:
                rospy.logwarn('No GPS fix available. Setting latitude, longitude, and altitude to 0.')
                point = Point(x=0, y=0, z=0)
        else:
            point = Point(x = current_fix.longitude, y=current_fix.latitude, z=current_fix.altitude)
        result = CategoricalObservation(header=msg.header, point=point, obs=obs)
        self.sgdrf_obs_publisher.publish(result)


def main():
     node = Node()
     node.spin()


if __name__ == "__main__":
    main()
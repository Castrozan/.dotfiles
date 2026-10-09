import QtQuick
import QtTest
import "../../../../quickshell/bar/program-configuration/dashboard/components"

Item {
    id: root

    QtObject {
        id: service
        property int refCount: 0
    }

    Component {
        id: activityComponent
        ServiceActivity {}
    }

    TestCase {
        name: "ServiceActivity"

        function cleanup() {
            compare(service.refCount, 0);
        }

        function test_initially_active_acquires_and_destroy_releases() {
            const activity = activityComponent.createObject(root, {
                service,
                active: true
            });
            verify(activity !== null);
            compare(service.refCount, 1);
            activity.destroy();
            wait(0);
            compare(service.refCount, 0);
        }

        function test_inactive_consumer_does_not_release() {
            const activity = activityComponent.createObject(root, {
                service,
                active: false
            });
            compare(service.refCount, 0);
            activity.destroy();
            wait(0);
            compare(service.refCount, 0);
        }

        function test_repeated_activation_is_balanced() {
            const activity = activityComponent.createObject(root, {
                service,
                active: false
            });
            for (let iteration = 0; iteration < 20; iteration++) {
                activity.active = true;
                compare(service.refCount, 1);
                activity.active = true;
                compare(service.refCount, 1);
                activity.active = false;
                compare(service.refCount, 0);
                activity.active = false;
                compare(service.refCount, 0);
            }
            activity.destroy();
            wait(0);
        }

        function test_consumers_share_service_without_stealing_references() {
            const first = activityComponent.createObject(root, {
                service,
                active: true
            });
            const second = activityComponent.createObject(root, {
                service,
                active: true
            });
            compare(service.refCount, 2);
            first.active = false;
            compare(service.refCount, 1);
            first.destroy();
            wait(0);
            compare(service.refCount, 1);
            second.destroy();
            wait(0);
            compare(service.refCount, 0);
        }

        function test_destroy_after_deactivation_does_not_release_twice() {
            const activity = activityComponent.createObject(root, {
                service,
                active: true
            });
            activity.active = false;
            compare(service.refCount, 0);
            activity.destroy();
            wait(0);
            compare(service.refCount, 0);
        }
    }
}
